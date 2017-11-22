from enum import IntEnum
from typing import NewType

Reqid = NewType('Reqid', int)
Seqno = NewType('Seqno', int)
View  = NewType('View',  Seqno)


class TaskType(IntEnum):
    NONE      = 0
    CONN_MADE = 1
    CONN_LOST = 2
    PEER_MSG  = 3
    PEER_ERR  = 4

class Task():
    def __init__(self, type:TaskType, item):
        self.type = type
        self.item = item
