from .principal import Principal
from .node import Node
from .types import TaskType, Task

class Replica(Node):
    def __init__(self,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.replica_principals[self.index]

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
