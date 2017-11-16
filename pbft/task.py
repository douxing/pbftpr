from enum import IntEnum

class TaskType(IntEnum):
    CONN_MADE = 1
    CONN_LOST = 2
    PEER_MSG  = 3
    PEER_ERR  = 4
    TIMER     = 5

class Task():
    def __init__(self, type:TaskType, item):
        self.type = type
        self.item = item
