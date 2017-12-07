import hashlib
import secrets

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Reqid
from .base_message import BaseMessage

class NewKey(BaseMessage):

    content_sedes = List([
        big_endian_int, # sender index
        big_endian_int, # timestamp
        big_endian_int, # extra with sender type
        CountableList(raw), # [k(j, i)]
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(signature)
    ])

    def __init__(self,
                 sender:int, reqid:Reqid,
                 extra, hmac_keys):
        """Session key
        """
        super().__init__()

        self.sender = sender
        self.reqid = reqid
        self.extra = extra
        self.hmac_keys = hmac_keys

        self.content = None
        self.auth = None
        self.payload = None

        self.from_addr = None

    def verify(self, peer_principal):
        return peer_principal.verify(self.content_digest, self.auth)

    def __str__(self):
        return '{}:{}\n{}\n{}\n{}'.format(self.sender, self.reqid,
                                          self.extra, self.hmac_keys,
                                          self.auth)

    @property
    def content_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.sender).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update('{}'.format(self.extra).encode())
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

        extra = 0
        if node.type is 'Client':
            extra |= 1 << 4

        message = cls(node.sender, node.next_reqid(), extra, hmac_keys)
        message.content = rlp.encode([message.sender, message.reqid,
                                       message.extra, message.hmac_keys],
                                      cls.content_sedes)

        message.auth = node.principal.sign(message.content_digest)
        message.payload = rlp.encode([message.content, message.auth],
                                      cls.payload_sedes)
        return message

    @classmethod
    def from_payload(cls, payload, addr, _node):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)

            [sender, reqid, extra, hmac_keys] = (
                rlp.decode(content, cls.content_sedes))

            message = cls(sender, reqid, extra, hmac_keys)
            message.content = content
            message.auth = auth
            message.payload = payload
            message.from_addr = addr

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
