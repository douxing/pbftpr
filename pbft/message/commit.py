import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Configuration as conf
from .base_message import BaseMessage
from .request import Request

class Commit():
    def __init__(self):
        pass


    @classmethod
    def from_replica(cls):
        pass

    @classmethod
    def from_payload(cls, payload, addr, _node):
        pass
