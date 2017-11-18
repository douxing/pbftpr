import asyncio

from .types import TaskType, Task

class DatagramServer(asyncio.DatagramProtocol):
    def __init__(self, node):
        self.node = node
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.node.notify(Task(TaskType.CONN_MADE, transport))

    def connection_lost(self, exc):
        """Lost connection

        There must something happened, stop the loop.
        """
        self.transport = None
        asyncio.ensure_future(
            self.node.notify(Task(TaskType.CONN_LOST, exc)))
        
    def datagram_received(self, data, addr):
        """Messages are node kind specific
        """
        self.node.notify(Task(TaskType.PEER_MSG, (data, addr)))

    def error_received(self, exc):
        # print('Node transport error: {}'.format(exc))
        asyncio.ensure_future(
            self.node.notify(Task(TaskType.PEER_ERR, exc)))

    def sendto(data:bytes, addr):
        self.transport.sendto(data, addr)
