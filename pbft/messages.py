from enum import IntEnum

import rlp import Serializable
from rlp.sedes import big_endian_int, text, ListSedes

class MessageTag(IntEnum):
    FREE_MSSAGE = 0
    REQUEST = 1
    REPLY = 2
    PRE_PREPARE = 3
    PREPARE = 4
    COMMMIT = 5
    CHECKPOINT = 6
    STATUS = 7
    VIEW_CHANGE = 8
    NEW_VIEW = 9
    VIEW_CHANGE_ACK = 10
    NEW_KEY = 11
    META_DATA = 12
    META_DATA_D = 13
    DATA = 14
    FETCH = 15
    QUERY_STABLE = 16
    REPLY_STABLE = 17

class Message():
    def __init__(self, tag:MessageTag):
        self.payload = None
