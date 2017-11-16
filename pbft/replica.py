import binascii

from .principal import Principal
from .node import Node
from .task import TaskType, Task

class Replica(Node):
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

        super().__init__(replica_principals = replica_principals,
                         *args, **kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.replica_principals[self.index]

    @property
    def is_valid(self):
        return super().is_valid

    async def handle(self, task:Task) -> bool:
        # print('task is {}'.format(task))

        if task.type == TaskType.CONN_MADE:
            pass
        elif task.type == TaskType.CONN_LOST:
            pass
        elif task.type == TaskType.PEER_MSG:
            pass
        elif task.type == TaskType.PERR_ERR:
            pass
        elif task.type == TaskType.TIMER:
            pass
        else:
            pass

        return True # continue loop
