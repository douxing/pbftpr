import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Reqid
from .message_tag import MessageTag
from .base_message import BaseMessage

class Request(BaseMessage):

    content_sedes = List([
        big_endian_int, # sender index
        big_endian_int, # timestamp(reqid)
        big_endian_int, # extra bitmap
        big_endian_int, # full replier
        raw, # command
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(authenticators or signature)
    ])

    def __init__(self, sender:int, reqid:Reqid, extra:int,
                 full_replier:int, command:bytes):
        """
        :extra bit 1: 0 readwrite,          1 readonly
               bit 2: 0 authenticators,     1 signature
               bit 5: 0 send from replica   1 send from client
               bit 6: 0 full replier,       1 reply from all
                        this flag is used for there is no -1 in rlp encoding
        :command set by users
        :auth bytes(signature) or [hmac_sha256...](authenticators)
        :full_replier ignored if extra & 1 << 5 is set (reply from all)
        """

        self.sender = sender
        self.reqid = reqid
        self.extra = extra
        self.full_replier = full_replier

        self.command = command

        self.content = None
        self.auth = None
        self.payload = None

        self.from_addr = None

    @property
    def readonly(self):
        return True if self.extra & 1 else False

    @readonly.setter
    def readonly(self, val):
        if val:
            self.extra |= 1
        else:
            self.extra &= ~1

    @property
    def use_signature(self):
        return True if self.extra & 2 else False

    @use_signature.setter
    def use_signature(self, val):
        if val:
            self.extra |= 2
        else:
            self.extra &= ~2

    @property
    def reply_from_all(self):
        return True if self.extra & 1 << 5 else False

    @reply_from_all.setter
    def reply_from_all(self, val):
        if val:
            self.extra |= 1 << 5
        else:
            self.extra &= ~(1 << 5)

    @property
    def command_digest(self):
        """compute digest for command
        """
        d = hashlib.sha256()
        # dx: i don't think, node_id, reqid is useful?
        # so I am commenting them out...
        # d.update('{}'.format(self.sender).encode())     # useless
        # d.update('{}'.format(self.reqid).encode())     # useless
        # dx: command only is just enough
        d.update(self.command)                           # useful
        return d.digest()

    @property
    def content_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.sender).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update('{}'.format(self.extra).encode())
        d.update('{}'.format(self.full_replier).encode())
        d.update(self.command_digest) # includes command and len(command)
        return d.digest()

    def authenticate(self, node):
        if self.use_signature:
            self.auth = node.principal.sign(self.content_digest)
        else:
            self.auth = node.gen_authenticators(self.content_digest)

        return self.auth

    def verify(self, node, peer_principal):
        pp = peer_principal

        if self.use_signature:
            return pp.verify(self.content_digest, self.auth)

        if len(node.replica_principals) != len(self.auth):
            return False

        # for request, we use 'out' key for the authentication
        return (pp.gen_hmac('out', self.content_digest)
                == self.auth[node.sender])

    @classmethod
    def from_none(cls):
        return cls(None, None, None, None, None)

    @classmethod
    def from_node(cls, node, readonly:bool,
                  use_signature:bool, reply_from_all:bool,
                  full_replier:int, command:bytes):

        extra = 0
        if readonly:
            extra |= 1
        if use_signature:
            extra |= 2
        if node.type is 'Client':
            extra |= 1 << 4
        if reply_from_all:
            extra |= 1 << 5

        message = cls(node.sender, node.next_reqid(), extra,
                      full_replier, command)


        message.content = rlp.encode([
            message.sender, message.reqid, message.extra,
            message.full_replier, message.command,
        ], message.content_sedes)

        message.authenticate(node)

        if message.use_signature:
            auth = message.auth
        else:
            auth = rlp.encode(message.auth,
                              cls.authenticators_sedes)

        message.payload = rlp.encode([message.content, auth],
                                     message.payload_sedes)
        return message

    @classmethod
    def from_payload(cls, payload, addr):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)
            [sender, reqid, extra, full_replier, extra, command] = (
                rlp.decode(content, cls.content_sedes))

            message = cls(sender, reqid, extra, full_replier, command)

            message.content = content
            if message.use_signature:
                message.auth = auth
            else:
                message.auth = rlp.decode(auth, cls.authenticators_sedes)
            message.payload = payload
            message.from_addr = addr

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
