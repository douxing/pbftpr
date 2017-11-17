import secrets

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..types import Reqid
from .message import MessageTag, BaseMessage

class NewKey(BaseMessage):

    hmac_nounce_length = 32

    contents_sedes = List([
        big_endian_int, # sender type
        big_endian_int, # sender index
        CountableList(raw), # [k(j, i)]
        big_endian_int, # timestamp
    ])

    payloads_sedes = List([
        raw, # contents
        raw, # signature
    ])

    def __init__(self,
                 node_type:int,
                 index:int,
                 reqid:Reqid,
                 *args, **kwargs):
        """Session key
        """
        self.node_type = node_type
        self.index = index
        self.reqid = reqid
        self.hmac_keys = []
        self.signature = None

        self.contents = None
        self.payloads = None
        
        super().__init__(*args, **kwargs)

    def gen_contents(self):
        if not self.hmac_keys:
            raise ValueError('invalid hmac_keys')

        self.contents = b''
        self.contents += rlp.encode(
            [self.node_type, self.index, self.hmac_keys, self.reqid],
            self.contents_sedes)

        return self.contents

    def gen_payloads(self):
        """Gerenate payloads from contents and signature
        """
        if type(self.contents) is not bytes:
            raise ValueError('invalid contents')
        elif not self.signature:
            raise ValueError('invalid signature')

        self.payloads = rlp.encode([self.contents, self.signature],
                                   self.payloads_sedes)

        return self.payloads

    @classmethod
    def parse(cls, frame:bytes):
        try:
            obj = rlp.decode(frame, cls.raw_sedes)
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))

        return obj
