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

        # request digests -> requests
        # self.requests = dict()

        # pending requests, all are full requests
        # principal -> [request]
        self.rw_requests = collections.OrderedDict()
        self.ro_requests = collections.OrderedDict()
        
        self.plog = PrepareCertificateLog(self.f,
                                          conf.checkpoint_max_out,
                                          1)
        
        # (sender_type, sender_index, reqid, commmand_digest) => request
        # self.inplog_requests = dict()

        self.replies = dict() # principal -> reply

        self.limbo = False # start view change but has NO new view

        self.seqno = Seqno(0) # used when this is primary

        self.last_stable = Seqno(0)
        self.low_bound = Seqno(0) # used for what?

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
            print('new_key timestamp failure: {}'.format(
                pp.index
            ))
            return

        # finally, update peer_principal
        pp.outkey = outkey
        pp.outkey_reqid = new_key.reqid

        print_new_key(new_key, pp)

    def recv_request(self, request, peer_principal):
        assert request.index == peer_principal.index
        pp = peer_principal

        # firstly, verify auth
        if self.has_new_view:
            if not request.verify(self, pp):
                return
        else:
            # TODO: it might be my fault?
            return

        # init attributes
        request.pre_prepare = None # pre_prepare it belong

        if (request.sender_type is Node.client_type):
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

                requests.insert(insert_index, request)
                self.rw_requests[pp] = requests
                self.rw_requests.move_to_end(pp)

                if self.principal is self.primary:
                    self.send_pre_prepare()
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

    def send_pre_prepare(self):
        assert self.principal is self.primary

        if not len(self.rw_requests) or not self.has_new_view:
            # 1. requests queue should NOT empty
            # 2. has new view
            return

        next_seqno = self.seqno + 1
        if not (next_seqno <= self.last_executed + consts.congestion_window
                and next_seqno <= self.last_stable + checkpoint_max_out):
            return # window is too narrow

        self.seqno = next_seqno # use new sequence number
        pre_prepare = PrePrepare.from_node(self)
        send(pre_prepare, 'ALL_REPLICAS')


    def recv_pre_prepare(self, pre_prepare):
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
