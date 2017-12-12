import binascii
import collections
import datetime
import traceback

from .principal import Principal
from .node import Node

from .basic import Reqid, Seqno, View, TaskType, Task, Configuration as conf
from .timer import Timer
from .log   import Log
from .utils import print_new_key, print_task

class Replica(Node):
    type = 'Replica'

    def __init__(self,
                 private_key, public_key,
                 status_interval:int,
                 view_change_interval:int,
                 recovery_interval:int,
                 idle_interval:int,
                 replica_principals = [],
                 *args, **kwargs):

        super().__init__(replica_principals = replica_principals,
                         *args, **kwargs)

        self.index = None # this is not a consensus replia
        for index, p in enumerate(replica_principals):
            if p.public_key == public_key:
                self.index = index
                p.private_key = private_key

        self.status_timer = Timer(status_interval / 1000.0,
                                  self.status_handler)
        self.view_change_timer = Timer(view_change_interval / 1000.0,
                                       self.view_change_handler)
        self.recovery_timer = Timer(recovery_interval / 1000.0,
                                    self.recovery_handler)
        self.idle_timer = Timer(recovery_interval / 1000.0,
                                self.idle_handler)

        # self.pending_requests = dict()

        # stale requests, all are full requests
        # principal -> [request]
        self.rw_requests = collections.OrderedDict()
        self.ro_requests = collections.OrderedDict()

        self.plog = PrepareCertificateLog(self, conf.checkpoint_max_out, 1)

        # (sender_type, sender_index, reqid, commmand_digest) => request
        # self.inplog_requests = dict()

        self.replies = dict() # principal -> reply

        self.limbo = False # start view change but has NO new view

        self.seqno = Seqno(0) # used when this is primary

        self.last_stable = Seqno(0)
        # self.low_bound = Seqno(0) # used for what?

        self.last_prepared = Seqno(0)

        # last commited seqno
        self.last_executed = Seqno(0)
        # last prepared seqno, this number is
        # either == self.last_executed
        # or     == self.last_executed + 1
        self.last_tentative_execute = Seqno(0)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.replica_principals[self.index]

    @property
    def is_valid(self):
        return super().is_valid

    @property
    def has_new_view(self):
        """this replica has complete new-view
        information for the current view
        """
        return self.view == 0 or True # TODO: more conditions

    def status_handler(self):
        pass

    def view_change_handler(self):
        pass

    def recovery_handler(self):
        pass

    def idle_handler(self):
        pass

    def start_view_change_timer(self):
        if (self.view_change_timer
            and not self.view_change_timer.done()):

    def execute_readonly(self, request):
        return True

    def execute_prepared(self):
        return True

    def execute_committed(self):
        return True


    def recv_new_key(self, new_key, peer_principal):
        assert new_key.index == peer_principal.index
        pp = peer_principal

        # firstly, verify signature
        if not new_key.verify(pp):
            print('new_key verification failure: {}'.format(
                pp.index
            ))
            return

        # secondly, extract outkey
        outkey = self.principal.decrypt(new_key.hmac_keys[self.index])
        if not outkey:
            print('new_key outkey failure: {}'.format(
                pp.index
            ))
            return

        # thirdly, check timestamp(reqid)
        if new_key.reqid <= pp.outkey_reqid:
            print('new_key timestamp failure: {}'.format(pp.index))
            return

        # finally, update peer_principal
        pp.outkey = outkey
        pp.outkey_reqid = new_key.reqid

        print_new_key(new_key, pp)

    def recv_request(self, request, peer_principal):
        assert request.index == peer_principal.index
        pp = peer_principal

        # verify auth
        if not request.command or not request.verify(self, pp):
            return

        if not self.has_new_view:
            # TODO: save for next view?
            return

        # init attributes
        request.pre_prepare = None # pre_prepare it belong

        if (request.sender_type is 'Client'):
            if request.readonly:
                if not execute_readonly(request):
                    # if failed, then push to the queue
                    # will try to execute it later
                    principal = self.client_principals[request.index]
                    self.ro_requests[principal] = request
                    self.ro_requests.move_to_end(principal)

                # return regardless of the result
                return

            # this is a read-write request from client
            last_reply_reqid = (self.replies[pp].reqid if
                                pp in self.replies else -1)
            if last_reply_reqid < request.reqid:
                # firstly, check whether this request is in pre_prepare
                req = self.plog.get_request(request)
                if req:
                    # found request in pre_prepare
                    # let's update insignificant informations
                    if req.consensus_digest != request.consensus_digest:
                        return # bad request TODO: log

                    pcert = self.plog[req.seqno]
                    # when pcert.add_pre_prepare
                    # pcert has updated plog.requests
                    assert pcert.pre_prepare
                    # if prepared, last_reply_reqid >= request.reqid
                    assert not pcert.is_prepared

                    if self.principal is self.primary:
                        if req.change_by_primary(request, self):
                            # pre_prepare.requests has been updated
                            # find no responsers and resend pre_prepare
                            pcert.pre_prepare.gen_payload(self) # re-auth
                            dest = []
                            for p in self.replica_principals:
                                if (p is not self.principal
                                    and p.index not in pcert.prepares):
                                    dest.append(p)
                            self.sendto(pcert.pre_prepare, dest)
                        # else:
                        #   TODO: if waited for too long, resend pre_prepare
                        #         but in fact this should be done by client
                    else:
                        # this is a backup
                        if req.change_by_backup(request.self):
                            # if req.command is None, then it will be assigned
                            # to request.command, if not, commands should also
                            # be the same, for consensus_digests is the same
                            assert req.command == request.command

                            if pcert.is_pre_prepared:
                                assert pcert.my_prepare
                                self.sendto(pcert.my_prepare, self.primary)
                            else if pcert.pre_prepare.is_requests_verified:
                                self.new_and_send_prepare(pcert)

                    return

                # if not in pre_prepare, insert into pending queue
                # and will be moved to the end of the queue

                requests = self.rw_requests.get(pp, [])
                # TODO: use bisect?
                insert_index = len(requests)
                for i, r in enumerate(requests):
                    if r.reqid < request.reqid:
                        continue
                    elif r.reqid == request.reqid:
                        if r.consensus_digest == request.consensus_digest:
                            r.change_by_primary(request, self)
                        return
                    else:
                        # r.reqid > request.reqid
                        insert_index = i
                        break

                if insert_index == len(requests):
                    request.pre_prepare_candidate = True
                    if requests:
                        requests[-1].pre_prepare_candidate = False
                else:
                     request.pre_prepare_candidate = False


                requests.insert(insert_index, request)
                self.rw_requests[pp] = requests
                self.rw_requests.move_to_end(pp)

                if self.principal is self.primary:
                    self.new_and_send_pre_prepare()
                else if not self.limbo:
                    send(request, self.primary)
                    # TODO: view change timer

            elif last_reqid == request.reqid:
                assert pp in self.replies
                reply = self.replies.get(pp)
                reply.view = self.view
                p = self.find_sender(reply)
                self.sendto(reply, p)

                # TODO: send reply
                # TODO: start view change timer if ...

        # TODO: replica request

    def new_and_send_pre_prepare(self):
        assert self.principal is self.primary

        if not len(self.rw_requests) or not self.has_new_view:
            # 1. requests queue should NOT empty
            # 2. has new view
            return

        new_seqno = self.seqno + 1
        if not (new_seqno <= self.last_executed + consts.congestion_window
                and new_seqno <= self.last_stable + checkpoint_max_out):
            return # window is too narrow

        self.seqno = new_seqno # use new sequence number

        pre_prepare = PrePrepare.from_primary(self, False)

        # add pre_prepare into plog
        pcert = self.plog[new_seqno]
        assert not pcert.pre_prepare

        send(pre_prepare, 'ALL_REPLICAS')
        pre_prepare.mine = True
        pcert.add_pre_prepare(pre_prepare)

    def in_proper_view(self, message):
        """
        :message: of type PrePrepare, Prepare, Commit
        """
        offset = message.seqno - self.last_stable
        if (offset > 0
            and offset <= conf.checkpoint_max_out
            and message.view == self.view):
            return True

        # TODO: send_status as negative ack

        return False

    def recv_pre_prepare(self, pre_prepare, peer_principal):
        if pcert.pre_prepare:
            # old pre_prepare dominates
            if (pcert.pre_prepare.view == pre_prepare.view
                and pcert.pre_prepare.seqno == pre_prepare.seqno
                and (pcert.pre_prepare.consensus_digest
                     == pre_prepare.consensus_digest)):
                pass
        elif pre_prepare.verify(self, peer_principal):
            pass
        elif pcert.prepare_count[pre_prepare.consensus_digest] >= self.f:
            # for liveness
            # plus this pre_prepare, we have f + 1 votes
            pass
        else
            return # TODO: log

        if self.principal == self.primary:
            return # i am the boss!
        elif not self.in_proper_view(pre_prepare)):
            return # TODO: send other messages? like fetch?

        if not self.has_new_view:
            return # TODO: add missing?

        pcert = self.plog[pre_prepare.seqno]
        changed = False
        if pcert.pre_prepare:
            for i, r in enumerate(pre_prepare.requests):
                if r.verify():
                    req = pcert.pre_prepare.requests[i] # old request
                    # (pcert.pre_prepare.consensus_digest
                    # == pre_prepare.consensus_digest) implies:
                    assert r.consensus_digest == req.consensus_digest
                    if req.change_by_backup(r, self):
                        changed = True
                # else:
                #   nothing to be done, just wait for client's request
        else:
            # new verified per_prepare
            # handle big requests
            for r in pre_prepare.requests:
                r.verify()
                p = self.find_sender(r)
                if not p:
                    continue # TODO: error?
                rs = node.rw_requests.get(p, [])
                for i, req in enumerate(rs):
                    if req.reqid == r.reqid:
                        r.change_by_backup(req, self)
                        rs.pop(i)
                        break

            pcert.add_pre_prepare(pre_prepare)
            changed = True

        # the above code ensures:
        assert pcert.pre_prepare

        if pcert.is_pre_prepared:
            # this is not primary, so
            assert pcert.my_prepare
            # resend my prepare
            self.sendto(pcert.my_prepare, self.primary)
        elif changed:
            assert not pcert.my_prepare
            if pcert.pre_prepare.is_requests_verified:
                self.new_and_send_prepare(pcert)

    def new_and_send_prepare(self, pcert):
        """
        """
        pre_prepare = pcert.pre_prepare

        assert pre_prepare and pre_prepare.is_requests_verified:
        assert not pcert.is_pre_prepared # not pcert.my_prepare

        prepare = Prepare.from_backup(self, pre_prepare,
                                      pre_prepare.view, pre_prepare.seqno,
                                      False,
                                      pre_prepare.consensus_digest)

        self.sendto(prepare, 'ALL_REPLICAS')
        changed = pcert.add_prepare(prepare):
        assert changed

        if pcert.is_prepared:
            self.new_and_send_commit(pcert)

    def recv_prepare(self, prepare, peer_principal):
        if (not prepare.verify(self, peer_principal)
            or prepare.sender == self.primary.index):
            return
        elif not self.in_proper_view(prepare):
            return # TODO: send other messages? like fetch?
        elif not self.has_new_view:
            return # TODO: add missing?

        pcert = self.plog[prepare.seqno]
        prepared = pcert.is_prepared
        if pcert.add_prepare(preprare):
            # received a valid vote
            if not prepared and pcert.is_prepared:
                # this is the key note
                self.new_and_send_commit(pcert)                    

    def new_and_send_commit(self, pcert):
        assert pcert.is_prepared # count of prepare == 2f
        assert self.index not in pcert.commits

        pre_prepare = pcert.pre_prepare
        commit = Commit.from_replica(self, pre_prepare.view,
                                     pre_prepare.seqno)

        self.sendto(commit, 'ALL_REPLICAS')
        changed = pcert.add_commit(commit)
        assert changed

        if pcert.is_committed:
            self.execute_committed()
        else:
            self.execute_prepared()

    def recv_commit(self. commit, peer_principal):
        if not commit.verify(self, peer_principal):
            return
        elif not self.in_proper_view(commit):
            return # TODO: send other messages? like fetch?
        elif not self.has_new_view:
            return # TODO: add missing?

        # what if i am primary and received a commit
        # for non-existant pre_prepare ?

        pcert = self.plog[commit.seqno]
        committed = pcert.is_committed
        if pcert.add_commit(commit): 
            if not committed and pcert.is_committed:
                self.execute_committed()

    def notify(self, task:Task):
        self.loop.create_task(self.task_queue.put(task))

    def recv_message(self, message):
        try:
            receiver = getattr(self, 'recv_{}'.format(message.tag.snake_name))

            principal = self.find_sender(message)
            if not principal:
                raise ValueError('no valid principal')

            receiver(message, principal)
        except:
            traceback.print_exc() # TODO: log

    async def handle(self, task:Task):
        print_task(task)

        if task.type == TaskType.CONN_MADE:
            pass # nothing to be done
        elif task.type == TaskType.CONN_LOST:
            raise IOError('connection lost')
        elif task.type == TaskType.PEER_MSG:
            data, addr = task.item
            message = self.parse_frame(data, addr)
            if message:
                self.recv_message(message)
            else
                print('invalid frame from: {}'.format(addr))

        elif task.type == TaskType.PEER_ERR:
            pass # nothing to be done
        else:
            raise ValueError('unknown task: {}'.format(task))

    async def fetch(self) -> Task:
        return await self.task_queue.get()

    async def fetch_and_handle(self):
        task = await self.task_queue.get()
        return await self.handle(task)

    def run(self):
        # create datagram server and fetch CONN_MADE
        self.transport, self.protocol = (
            self.loop.run_until_complete(self.listen))
        task = self.loop.run_until_complete(self.fetch())
        assert task.type == TaskType.CONN_MADE

        # start auth_timer
        self.auth_timer_handler()

        try:
            while True:
                self.loop.run_until_complete(self.fetch_and_handle())
        except:
            traceback.print_exc()
