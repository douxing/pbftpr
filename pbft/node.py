import asyncio
from datetime import datetime
import math
import sys
import traceback

from .types import Reqid, Seqno, View, TaskType, Task
from .datagram_server import DatagramServer
from .principal import Principal
from .message import MessageTag, BaseMessage, NewKey
from .utils import utcnow_reqid, print_new_key

class Node():

    replica_type = 1
    client_type  = 2

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

        self.reqid = utcnow_reqid()
        self.last_new_key = None

        self.listen = self.loop.create_datagram_endpoint(
            lambda: DatagramServer(self),
            local_addr=(self.principal.ip, self.principal.port))

        self.last_new_key = None
        self.auth_timer = None
        self.auth_interval = auth_interval / 1000.0 # in seconds

        super().__init__()

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

    def next_reqid(self) -> Reqid:
        self.reqid += 1
        return self.reqid

    def find_principal(self, message, addr):
        try:
            if message.node_type == self.replica_type:
                principal = self.replica_principals[message.index]
            elif message.node_type == self.client_type:
                principal = self.client_principals[message.index]

            assert principal.index == message.index

            # TODO: restrict addr in ip range?
            assert principal.addr == addr

            return principal
        except IndexError:
            traceback.print_exc()
        except:
            traceback.print_exc()

        return None

    def auth_handler(self, sleep_task = None):
        self.loop.call_soon(self.send_new_key)

    def gen_authenticators(self, hash_bytes):
        authenticators = []
        for p in self.replica_principals:
            if p is self.principal:
                authenticators.append(b'')
            else:
                authenticators.append(p.gen_hmac('out', hash_bytes))
        return authenticators

    def send_new_key(self):
        if __debug__:
            print('node send_new_key')

        new_key = NewKey.from_node(self)

        self.sendto(new_key, 'ALL_REPLICAS')
        self.last_new_key = new_key

        # reset self.auth_timer
        if self.auth_timer and not self.auth_timer.done():
            self.auth_timer.cancel()

        self.auth_timer = self.loop.create_task(
            asyncio.sleep(self.auth_interval, loop = self.loop))

        self.auth_timer.add_done_callback(self.auth_handler)

    def parse_frame(self, data, addr):
        try:
            tag, payloads = BaseMessage.parse_frame(data)
            cls = getattr(sys.modules[__name__], tag.name)
            message = cls.from_payloads(payloads)

            receiver = getattr(self,
                               'recv_{}'.format(MessageTag.snake_name(tag)))

            principal = self.find_principal(message, addr)
            if not principal:
                raise ValueError('no valid principal found')

            receiver(message, principal)
        except ValueError:
            if __debug__:
                traceback.print_exc()
            else:
                pass # TODO: log
        except:
            if __debug__:
                traceback.print_exc()
            else:
                pass # TODO: log

    def notify(self, task:Task):
        self.loop.create_task(self.task_queue.put(task))

    def sendto(self, data:bytes, dest):
        if isinstance(data, BaseMessage):
            data = data.frame

        if dest == 'ALL_REPLICAS':
            for p in self.replica_principals:
                self.sendto(data, p)
        elif dest == 'ALL_CLIENTS':
            for p in self.client_principals:
                self.sendto(data, p)
        else:
            # unicast to addr
            if type(dest) is type(self.principal):
                if dest is self.principal:
                    return # don't send to myself

                dest = dest.addr

            self.transport.sendto(data, dest)

    async def handle(self, task:Task):
        """Handle all kinds of tasks
        """
        raise NotImplementedError

    async def fetch_and_handle(self):
        task = await self.task_queue.get()
        return await self.handle(task)

    def run(self):
        raise NotImplementedError
