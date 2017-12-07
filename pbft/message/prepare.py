import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Configuration as conf
from .base_message import BaseMessage
from .request import Request

class Prepare():

    content_sedes = List([
        big_endian_int, # view
        big_endian_int, # seqno
        big_endian_int, # extra
        big_endian_int, # sender
        raw, # consensus_digest of pre_prepare
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(signature)
    ])

    def __init__(self, view, seqno, extra,
                 sender, consensus_digest):
        self.view  = view
        self.seqno = seqno
        self.extra = extra
        self.sender = sender
        self.consensus_digest = consensus_digest

        self.content = None
        self.auth = None
        self.payload = None

    @property
    def use_signature(self):
        return True if self.extra & 2 else False

    @use_signature.setter
    def use_signature(self, val):
        if val:
            self.extra |= 2
        else:
            self.extra &= ~2

    def authenticate(self):
        pass

    def verify(self):
        pass

    @classmethod
    def from_backup(cls, backup, view, seqno,
                    use_signature:bool, consensus_digest):

        extra = 0
        if use_signature:
            extra |= 2

        return cls(view, seqno, extra,
                   backup.index, consensus_digest)

    @classmethod
    def from_payload(cls, payload, addr, _node):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)
            [view, seqno, extra, sender, consensus_digest] = rlp.decode(
                content, cls.content_sedes)

            message = cls(view, seqno, extra, sender, consensus_digest)
            message.content = content
            message.auth = auth
            message.payload = payload

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
