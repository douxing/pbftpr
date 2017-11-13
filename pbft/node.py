import asyncio
from datetime import datetime
import math

from .datagram_server import DatagramServer
from .principal import Principal
from .types import Reqid, Seqno, View, TaskType, Task
from .messages import NewKey

class Node():
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
        self.task_queue = asyncio.Queue(loop=self.loop)

        self.reqid = Reqid(math.floor(datetime.utcnow().timestamp() * 10**9))
        self.last_new_key = None

        self.listen = self.loop.create_datagram_endpoint(
            lambda: DatagramServer(self),
            local_addr=(self.principal.ip, self.principal.port))

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

    async def notify(self, task:Task):
        await self.task_queue.put(task)

    def sendto(self, data, addr):
        pass


    async def handle(self, task:Task):
        """Handle all kinds of tasks
        """
        raise NotImplementedError

    async def fetch_and_handle_loop(self):
        res = True
        while res:
            task = await self.task_queue.get()
            res  = await self.handle(task)
            
    def run(self):
        _transport, _protocol = self.loop.run_until_complete(self.listen)
        self.loop.run_until_complete(self.fetch_and_handle_loop())
