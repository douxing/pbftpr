import asyncio
from datetime import datetime
import math
import sys

from .datagram_server import DatagramServer
from .principal import Principal
from .types import Reqid, Seqno, View
from .task import TaskType, Task
from .message import MessageTag, BaseMessage, NewKey

class Node():
    def __init__(self,
                 n:int, f:int,
                 auth_interval:int, # in milli seconds
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

        self.last_new_key = None
        self.auth_timer = None
        self.auth_interval = auth_interval / 1000.0 # in seconds

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

    def new_reqid(self) -> Reqid:
        self.reqid += 1
        return self.reqid

    def auth_handler(self, sleep_task = None):
        self.loop.call_soon(self.send_new_key)

    def send_new_key(self):
        if __debug__:
            print('node send_new_key')

        new_key = NewKey.from_principals(
            self.TYPE, self.index, self.new_reqid(),
            self.principal, self.replica_principals)
        
        self.sendto(new_key, 'ALL_REPLICAS')
        self.last_new_key = new_key

        # reset self.auth_timer
        if self.auth_timer and not self.auth_timer.done():
            self.auth_timer.cancel()

        self.auth_timer = self.loop.create_task(
            asyncio.sleep(self.auth_interval, loop = self.loop))

        self.auth_timer.add_done_callback(self.auth_handler)

    def recv_new_key(self, new_key):
        print('verify new key: {}'.format(new_key))

    def parse_frame(self, data, addr):
        if __debug__:
            sender_principal = None
            for p in self.replica_principals + self.client_principals:
                if (p.ip, p.port) == addr:
                    sender_principal = p
                    break

            if not sender_principal:
                print('reject to process unknown addr: {}'.addr)
                return
        
        try:
            tag, payloads = BaseMessage.parse_frame(data)
            cls = getattr(sys.modules[__name__], tag.name)
            message = cls.from_payloads(payloads)

            receiver = getattr(self,
                               'recv_{}'.format(MessageTag.snake_name(tag)))

            receiver(message)
        except ValueError as exc:
            print('parse frame value error: {}'.format(exc))
            return
        except BaseException as exc:
            print('parse frame error: {}'.format(exc))
            return

    def notify(self, task:Task):
        self.loop.create_task(self.task_queue.put(task))

    def sendto(self, data:bytes, addr):
        if isinstance(data, BaseMessage):
            data = data.frame

        if addr == 'ALL_REPLICAS':
            for p in self.replica_principals:
                self.sendto(data, (p.ip, p.port))
        elif addr == 'ALL_CLIENTS':
            for p in self.client_principals:
                self.sendto(data, (p.ip, p.port))
        else:
            # unicast to addr
            self.transport.sendto(data, addr)

    async def handle(self, task:Task):
        """Handle all kinds of tasks
        """
        raise NotImplementedError

    async def fetch_and_handle(self):
        task = await self.task_queue.get()
        return await self.handle(task)

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
