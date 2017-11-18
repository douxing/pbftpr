import binascii
import datetime

from .debug import pprint_task
from .principal import Principal
from .node import Node
from .task import TaskType, Task

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

    def recv_new_key(self, new_key, principal):
        # firstly, verify signature
        if not principal.verify(new_key.contents, new_key.signature):
            print('invalid signature: {}'.format(principal))

        # decode and assign outkey for the principal
        self.principal.outkey = self.principal.decrypt(
            new_key.hmac_keys[self.index])
        if self.principal.outkey_reqid < new_key.reqid:
            self.principal.outkey_reqid = new_key.reqid

    async def handle(self, task:Task) -> bool:
        pprint_task(task)

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
