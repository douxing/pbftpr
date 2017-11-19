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

    def recv_new_key(self, new_key, pp):
        """
        
        :pp peer_principal
        """
        try:
            assert new_key.index == pp.index

            # firstly, verify signature
            if not pp.verify(new_key.contents, new_key.signature):
                raise ValueError('invalid signature')

            # this comes fist, 'cause whenever decrypt failed,
            # decrypt will raise error, thus break the assignment
            outkey = self.principal.decrypt(new_key.hmac_keys[self.index])

            if pp.outkey_reqid < new_key.reqid:
                pp.outkey = outkey
                pp.outkey_reqid = new_key.reqid
            else:
                raise ValueError('invalid reqid(timestamp)')

            print_new_key(new_key, pp)
        except:
            if __debug__:
                traceback.print_exc()
            else:
                pass # TODO: log
            
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

        self.loop.create_task()

        while True:
            res = self.loop.run_until_complete(self.fetch_and_handle())
            if not res:
                break
