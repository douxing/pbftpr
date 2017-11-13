from .principal import Principal
from .node import Node
from .types import TaskType, Task

class Replica(Node):
    def __init__(self,
                 private_key, public_key,
                 replica_principals = [],
                 *args, **kwargs):

        self.index = None # this is not a consensus replia
        for index, p in enumerate(replica_principals):
            if p.public_key is public_key:
                self.index == index
                p.private_key = private_key

        super().__init__(*args, **kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.replica_principals[self.index]

    @property
    def is_valid(self):
        return super().is_valid

    async def handle(self, task:Task) -> bool:
        if task.type == TaskType.COMM_MADE:
            pass
        elif task.type == TaskType.COMM_LOST:
            pass
        elif task.type == TaskType.PEER_MSG:
            pass
        elif task.type == TaskType.PERR_ERR:
            pass
        elif task.type == TaskType.TIMER:
            pass
        else:
            pass

        print('task is {}'.format(task))

        return True # continue loop
