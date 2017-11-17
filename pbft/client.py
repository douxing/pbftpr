from .principal import Principal
from .node import Node
from .task import TaskType, Task

class Client(Node):
    TYPE = 2

    def __init__(self,
                 private_key:str, public_key:str,
                 client_principals = [],
                 *args, **kwargs):

        self.index = None
        for index, p in enumerate(client_principals):
            if p.public_key is public_key:
                self.index = index
                p.private_key = private_key

        super().__init__(client_principals = client_principals,
                         *args, **kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.client_principals[self.index]

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
