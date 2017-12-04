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

class Configuration:
    # replicas can handle this many before next requests
    congestion_window = 1

    # max request counts in pre prepare
    request_in_pre_prepare = 1

    pre_prepare_big_request_thresh = 80
    pre_prepare_content_thresh = 8196

    checkpoint_interval = 128
    checkpoint_max_out  = checkpoint_interval * 2



