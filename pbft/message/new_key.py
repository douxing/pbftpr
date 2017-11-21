import hashlib
import secrets

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..types import Reqid
from .base_message import BaseMessage

class NewKey(BaseMessage):

    contents_sedes = List([
        big_endian_int, # sender type
        big_endian_int, # sender index
        big_endian_int, # timestamp
        CountableList(raw), # [k(j, i)]
    ])

    payloads_sedes = List([
        raw, # contents
        raw, # auth(signature)
    ])

    def __init__(self,
                 node_type:int, index:int, reqid:Reqid, hmac_keys):
        """Session key
        """
        self.node_type = node_type
        self.index = index
        self.reqid = reqid
        self.hmac_keys = hmac_keys

        self.contents = None
        self.auth = None
        self.payloads = None

        super().__init__()

    def verify(self, peer_principal):
        return peer_principal.verify(self.contents_digest, self.auth)

    def __str__(self):
        return '{}:{}\n{}\n{}\n{}'.format(self.node_type, self.index,
                                          self.reqid, self.hmac_keys,
                                          self.auth)

    @property
    def contents_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.node_type).encode())
        d.update('{}'.format(self.index).encode())
        d.update('{}'.format(self.reqid).encode())
        for k in self.hmac_keys:
            d.update(k)
        return d.digest()

    @classmethod
    def from_node(cls, node):

        hmac_keys = []
        for p in node.replica_principals:
            if p is node.principal:
                nonce = p.zero_hmac_nounce
            else:
                nonce = p.gen_inkey()

            hmac_keys.append(p.encrypt(nonce))

        message = cls(node.type, node.index, node.next_reqid(), hmac_keys)
        message.contents = rlp.encode([message.node_type, message.index,
                                       message.reqid, message.hmac_keys],
                                      cls.contents_sedes)

        message.auth = node.principal.sign(message.contents_digest)
        message.payloads = rlp.encode([message.contents, message.auth],
                                      cls.payloads_sedes)
        return message

    @classmethod
    def from_payloads(cls, payloads):
        try:
            [contents, auth] = rlp.decode(payloads, cls.payloads_sedes)

            [node_type, index, reqid, hmac_keys] = (
                rlp.decode(contents, cls.contents_sedes))

            message = cls(node_type, index, reqid, hmac_keys)
            message.contents = contents
            message.auth = auth
            message.payloads = payloads

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
