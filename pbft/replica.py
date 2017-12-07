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
        self.last_executed = Seqno(0)
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

    def execute_commited(self):
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
        if not request.verify(self, pp):
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
                    if (req.consensus_digest != request.consensus_digest
                        or not req.command):
                        return # bad request TODO: log

                    if (self.principal is self.primary
                        and req.change_in_primary(request, self)):
                        pass # TODO: find no prepare and resend prepare
                    else:
                        if 
                            

                    if request.consensus_digest != req.consensus_digest:
                        return # old one dominates

                    pcert = self.plog[req.seqno]
                    if pre_prepare.update_request(request):
                        pass

                    req.command = request.command
                    

                    if not req.verified:
                        assert request.verified
                        req.verified = True

                    if request.reply_from_all:
                        req.reply_from_all = True

                    if request.full_replier == self.index:
                        req.full_replier = self.index


                    if (pre_prepare.verified_requests_count(self)
                        == len(pre_prepare.requests)):
                        if 
                        
                    return

                
                requests = self.rw_requests.get(pp, [])
                # TODO: use bisect?
                insert_index = len(requests)
                for i, r in enumerate(requests):
                    if r.reqid < request.reqid:
                        continue
                    elif r.reqid == request.reqid:
                        # duplicate, ignore this one
                        # TOOD: warning log if not the same
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
                reply = self.replies[pp]
                reply.view = self.view
                reply.sender = self.index

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
        assert not pcert.is_pre_prepared() # right?
        pcert.add_pre_prepare(pre_prepare, True)
        
        send(pre_prepare, 'ALL_REPLICAS')

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
        if not pre_prepare.verify(self, peer_principal):
            # TODO: log
            return

        if (self.principal == self.primary # i am the boss!
            or not self.in_proper_view(pre_prepare)):
            # TODO: log
            return

        if not self.has_new_view:
            # TODO: add missing?
            return

        pcert = self.plog[pre_prepare.seqno]
        if pcert.pre_prepare:
            # update pcert.pre_prepare if possible
            if (pcert.pre_prepare.view != pre_prepare.view
                or pcert.pre_prepare.seqno != pre_prepare.seqno
                or (pcert.pre_prepare.consensus_digest
                    != pre_prepare.consensus_digest)):
                return # old one dominates

            for i, r in enumerate(pre_prepare.requests):
                req = pcert.pre_prepare.requests[i] # old request
                req.change_in_backup(r, self)
        else:
            # new verified per_prepare
            # handle big requests
            pcert.add_pre_prepare(pre_prepare)
            for r in pre_prepare.requests:
                if r.auth:
                    # only interested in big requests
                    # which are sent directly from clients
                    continue

                for req in node.rw_requests:
                    if req.

                
            
        

    def send_prepare(self):
        pass

    def recv_prepare(self, prepare, peer_principal):
        pass

    def send_commit(self):
        pass

    def recv_commit(self. commit, peer_principal):
        pass
        
        


    

        



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
