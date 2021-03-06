import asyncio
from datetime import datetime
import math
import sys
import traceback

from .types import Reqid, Seqno, View, TaskType, Task
from .datagram_server import DatagramServer
from .principal import Principal
from .message import MessageTag, BaseMessage, NewKey, Request, Reply
from .timer import Timer
from .utils import utcnow_reqid, print_new_key

class Node():

    def __init__(self,
                 n:int, f:int,
                 auth_interval:int, # in milli seconds
                 replica_principals = [], client_principals = [],
                 *args, **kwargs):

        self.n = n
        self.f = f

        self.replica_principals = replica_principals
        self.client_principals = client_principals

        self.view = View(0)

        # use task queue to queue tasks
        self.task_queue = asyncio.Queue(loop=self.loop)

        self.reqid = utcnow_reqid()
        self.last_new_key = None

        self.listen = self.loop.create_datagram_endpoint(
            lambda: DatagramServer(self),
            local_addr=(self.principal.ip, self.principal.port))

        self.last_new_key = None
        self.auth_timer = Timer(auth_interval / 1000.0,
                                self.auth_timer_handler)

        super().__init__(*args, **kwargs)

    @property
    def quorum(self):
        return self.f + (self.n - self.f) // 2 + 1

    @property
    def primary(self) -> Principal:
        index = self.view % self.n 
        return self.replica_principals[index]

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

    def find_sender(self, message):
        try:
            if message.sender_type == 'Replica':
                principal = self.replica_principals[message.sender]
            elif message.sender_type == 'Client':
                principal = self.client_principals[message.sender]

            assert principal.index == message.index

            # TODO: restrict addr in ip range?
            # assert principal.addr == message.from_addr

            return principal
        except IndexError:
            traceback.print_exc()
        except:
            traceback.print_exc()

    def gen_authenticators(self, hash_bytes):
        authenticators = []
        for p in self.replica_principals:
            if p is self.principal:
                authenticators.append(b'')
            else:
                authenticators.append(p.gen_hmac('out', hash_bytes))
        return authenticators

    def auth_timer_handler(self, _task = None):
        self.send_new_key()

        # reset self.auth_timer
        self.auth_timer.restart()

    def send_new_key(self):
        if __debug__:
            print('node send_new_key')

        new_key = NewKey.from_node(self)
        self.sendto(new_key, 'ALL_REPLICAS')
        self.last_new_key = new_key

    def parse_frame(self, data, addr):
        try:
            tag, payload = BaseMessage.parse_frame(data)
            cls = getattr(sys.modules[__name__], tag.name)
            message = cls.from_payload(payload, addr, self)
            return message
        except:
            traceback.print_exc() # TODO: log

    def notify(self, task:Task):
        self.loop.create_task(self.task_queue.put(task))

    def sendto(self, data:bytes, dest, include_self=False):
        if isinstance(data, BaseMessage):
            data = data.frame

        if dest is 'ALL_REPLICAS':
            self.sendto(data, self.replica_principals, include_self)
        elif dest is 'ALL_CLIENTS':
            self.sendto(data, self.client_principals, include_self)
        elif type(dest) is tuple or type(dest) is list:
            for d in dest:
                self.sendto(data, d, include_self)
        else:
            assert type(dest) is Principal:
            # unicast to addr
            if dest is self.principal and not include_self:
                return # don't send to myself

            dest = dest.addr
            self.transport.sendto(data, dest)
