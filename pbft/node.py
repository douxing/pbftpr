import asyncio
from datetime import datetime
import math

from .principal import Principal
from .types import Reqid, Seqno, View, TaskType, Task
from .messages import NewKey

class Node(asyncio.DatagramProtocol):
    def __init__(self,
                 n:int = 0, f:int = 0,
                 replica_principals = [], client_principals = [],
                 loop = asyncio.get_event_loop(),
                 *args, **kwargs):

        self.n = n
        self.f = f

        self.replica_principals = [p for p in replica_principals]
        self.client_principals = [p for p in client_principals]

        self.view = View(0)

        self.loop = loop
        # use task queue to queue tasks
        self.task_queue = asyncio.Queue(self.loop)

        self.reqid = Reqid(math.floor(datetime.utcnow().timestamp() * 10**9))
        self.last_new_key = None

        super().__init__(*args, **kwargs)

    @property
    def quorum(self):
        return self.f + (self.n - self.f) // 2 + 1

    @property
    def primary(self) -> int:
        return self.view % self.n

    @property
    def is_valid(self):
        if (self.f * 3 + 1 > self.n
            or len(self.replica_principals) < n
            or self.index == None):
            return False

        return True

    def new_reqid() -> Reqid:
        self.reqid += 1
        return self.reqid

    def send_new_key():
        pass

    def connection_made(self, transport):
        self.transport = transport
        self.task_queue.put(Task(TaskType.CONN_MADE, transport))

    def connection_lost(self, exc):
        """Lost connection

        There must something happened, stop the loop.
        """
        self.task_queue.put(Task(TaskType.CONN_LOST, exc))
        
    def datagram_received(self, data, addr):
        """Messages are node kind specific
        """

        # TODO: check addr?
        self.task_queue.put(Task(TaskType.PEER_MSG, data))

    def error_received(self, exc):
        # print('Node transport error: {}'.format(exc))
        self.task_queue.put(Task(TaskType.PEER_ERR, exc))

    async def handle(self, task:Task):
        """Handle all kinds of tasks
        """
        raise NotImplementedError

    async def fetch_and_handle_loop(self):
        res = True
        while res:
            task = await self.task_queue.get()
            res  = await handle(task)
        
    def run(self, loop = asyncio.get_event_loop()):
        loop.run_until_complete(self.fetch_and_handle_loop())
