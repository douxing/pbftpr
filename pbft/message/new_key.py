import secrets

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..types import Reqid
from .message import MessageTag, BaseMessage

class NewKey(BaseMessage):

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
                 node_type:int, index:int, reqid:Reqid, hmac_keys,
                 contents, signature, payloads):
        """Session key
        """
        self.node_type = node_type
        self.index = index
        self.reqid = reqid
        self.hmac_keys = hmac_keys

        self.contents = contents
        self.signature = signature
        self.payloads = payloads

        super().__init__()

    def __str__(self):
        return '{}:{}\n{}\n{}\n{}'.format(self.node_type, self.index,
                                       self.reqid, self.hmac_keys,
                                       self.signature)

    @classmethod
    def from_principals(cls,
                        node_type:int, index:int, reqid:Reqid,
                        principal, replica_principals):

        hmac_keys = []
        for p in replica_principals:
            if p is principal:
                nounce = p.zero_hmac_nounce
            else:
                nounce = p.gen_inkey()

            hmac_keys.append(p.encrypt(nounce))

        contents = rlp.encode([node_type, index, hmac_keys, reqid],
                              cls.contents_sedes)
        signature = principal.sign(contents)
        payloads = rlp.encode([contents, signature],
                              cls.payloads_sedes)

        return cls(node_type, index, reqid, hmac_keys,
                   contents, signature, payloads)

    @classmethod
    def from_payloads(cls, payloads):
        try:
            [contents, signature] = rlp.decode(payloads, cls.payloads_sedes)

            [node_type, index, hmac_keys, reqid] = (
                rlp.decode(contents, cls.contents_sedes))

            return cls(node_type, index, reqid, hmac_keys,
                       contents, signature, payloads)
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
