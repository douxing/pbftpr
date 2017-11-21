import binascii
import datetime
import traceback

from .principal import Principal
from .node import Node

from .types import Reqid, Seqno, View, TaskType, Task
from .utils import print_new_key, print_task

class Replica(Node):
    type = Node.replica_type

    def __init__(self,
                 private_key, public_key,
                 status_interval:int,
                 view_change_interval:int,
                 recovery_interval:int,
                 idle_interval:int,
                 replica_principals = [],
                 *args, **kwargs):

        self.index = None # this is not a consensus replia
        for index, p in enumerate(replica_principals):
            if p.public_key == public_key:
                self.index = index
                p.private_key = private_key

        self.status_interval = status_interval
        self.view_change_interval = view_change_interval
        self.recovery_interval = recovery_interval
        self.idle_interval = idle_interval

        super().__init__(replica_principals = replica_principals,
                         *args, **kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.replica_principals[self.index]

    @property
    def is_valid(self):
        return super().is_valid

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

        # firstly, verify signature
        if not request.verify(pp):
            print('request verification faillure: {}'.format(
                pp.index
            ))
            return

        print('------------------requst: {}'.format(request))

    async def handle(self, task:Task) -> bool:
        print_task(task)

        if task.type == TaskType.CONN_MADE:
            pass
        elif task.type == TaskType.CONN_LOST:
            pass
        elif task.type == TaskType.PEER_MSG:
            data, addr = task.item
            self.parse_frame(data, addr)
        elif task.type == TaskType.PERR_ERR:
            pass
        elif task.type == TaskType.TIMER:
            pass
        else:
            pass

        return True # continue loop

    def run(self):
        # create datagram server
        self.transport, self.protocol = self.loop.run_until_complete(self.listen)
        res = self.loop.run_until_complete(self.fetch_and_handle())

        assert res # receive CONN_MADE
        self.send_new_key()



        while True:
            res = self.loop.run_until_complete(self.fetch_and_handle())
            if not res:
                break
