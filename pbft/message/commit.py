import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Configuration as conf
from .base_message import BaseMessage
from .request import Request

class Commit():

    content_sedes = List([
        big_endian_int, # view
        big_endian_int, # seqno
        big_endian_int, # sender
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(signature)
    ])

    def __init__(self, view, seqno, extra, sender):
        self.view  = view
        self.seqno = seqno
        self.sender = sender

        self.content = None
        self.auth = None
        self.payload = None

    @classmethod
    def from_replica(cls, replica, view, seqno):
        return cls(view, seqno, replica.index)

    @classmethod
    def from_payload(cls, payload, addr, _node):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)
            [view, seqno, sender] = rlp.decode(content, cls.content_sedes)

            message = cls(view, seqno, sender)
            message.content = content
            message.auth = auth
            message.payload = payload

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
