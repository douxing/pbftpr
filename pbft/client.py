import traceback

from .types import Reqid, Seqno, View, TaskType, Task
from .message import Request, Reply
from .utils import print_task
from .principal import Principal
from .node import Node

class Client(Node):
    type = Node.client_type

    def __init__(self,
                 private_key:str, public_key:str,
                 client_principals = [],
                 *args, **kwargs):

        self.index = None
        for index, p in enumerate(client_principals):
            if p.public_key == public_key:
                self.index = index
                p.private_key = private_key

        self.current_request = None

        super().__init__(client_principals = client_principals,
                         *args, **kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.client_principals[self.index]

    async def handle(self, task:Task):
        print_task(task)
        res = None

        if task.type == TaskType.CONN_MADE:
            pass # nothing to be done
        elif task.type == TaskType.CONN_LOST:
            raise IOError('connection lost')
        elif task.type == TaskType.PEER_MSG:
            data, addr = task.item
            res = self.parse_frame(data, addr)
        elif task.type == TaskType.PEER_ERR:
            pass # nothing to be done
        else:
            raise ValueError('unknown task: {}'.format(task))

        return res

    async def fetch(self) -> Task:
        return await self.task_queue.get()        

    def send_request(self, request):
        if self.current_request:
            return False # do nothing

        r = request

        if r.readonly or len(r) > r.big_request_thresh:
            self.sendto(r, 'ALL_REPLICAS')
        else:
            self.sendto(r, self.primary)

        self.current_request = r

        # TODO: retransmit
        return True

    def recv_message(self):
        task = self.loop.run_until_complete(self.fetch())
        message = self.loop.run_until_complete(self.handle(task))
        return message


    def process_requests(self, reqs):
        # create datagram server
        self.transport, self.protocol = self.loop.run_until_complete(self.listen)
        task = self.loop.run_until_complete(self.fetch())
        assert task.type == TaskType.CONN_MADE

        # send key auth keys, thus we can push requests to replicas
        self.send_new_key()

        # send requests and recv replies one by one
        for request in reqs:
            if not self.send_request(request):
                print('error when send: {}'.format(request))

            try:
                while True:
                    message = self.recv_message()
                    if type(message) is not Reply:
                        print('message: {}: '.format(message))                    
                        continue

                    print('reply: {}: '.format(message))                    
                    

            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()

