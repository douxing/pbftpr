import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..types import Reqid
from .types import MessageTag
from .base_message import BaseMessage

class Request(BaseMessage):

    contents_sedes = List([
        big_endian_int, # sender type
        big_endian_int, # sender index
        big_endian_int, # timestamp(reqid)
        big_endian_int, # extra bitmap
        big_endian_int, # reply_to_all
        big_endian_int, # replier, meaningless if reply_to_all
        raw, # command
    ])

    payloads_sedes = List([
        raw, # contents
        raw, # auth(authenticators or signature)
    ])

    def __init__(self,
                 node_type:int, index:int,
                 reqid:Reqid, extra:int,
                 reply_to_all:int, replier:int,
                 command:bytes):
        """
        :extra bit 1: 0 readwrite,        1 readonly
               bit 2: 0 authenticators,   1 signature
        :command set by users
        :auth bytes(signature) or [hmac_sha256...](authenticators)
        :reply_to_all is used because there is no -1 in rlp encoding
        :replier      is meaningless if reply_to_all
        """

        self.node_type = node_type
        self.index = index
        self.reqid = reqid
        self.extra = extra
        self.reply_to_all = reply_to_all
        self.replier = replier


        self.command = command

        self.contents = None
        self.auth = None
        self.payloads = None

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
    def command_digest(self):
        """compute digest for command
        """
        d = hashlib.sha256()
        # dx: i don't think, node_id, reqid is useful?
        # so I am commenting them out...
        # d.update('{}'.format(self.node_type).encode()) # useless
        # d.update('{}'.format(self.index).encode())     # useless
        # d.update('{}'.format(self.reqid).encode())     # useless
        # dx: command only is just enough
        d.update(self.command)                           # useful
        return d.digest()

    @property
    def contents_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.node_type).encode())
        d.update('{}'.format(self.index).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update('{}'.format(self.extra).encode())
        d.update('{}'.format(self.reply_to_all).encode())
        d.update('{}'.format(self.replier).encode())
        d.update(self.command_digest) # includes command and len(command)
        return d.digest()

    def authenticate(self, node):
        if self.use_signature:
            self.auth = node.principal.sign(self.contents_digest)
        else:
            self.auth = node.gen_authenticators(self.contents_digest)

        self.contents = rlp.encode([
            self.node_type, self.index, self.reqid, self.extra,
            self.reply_to_all, self.replier, self.command,
        ], self.contents_sedes)

        self.payloads = rlp.encode([
            self.contents, self.auth
        ], self.payloads_sedes)

    def verify(self, node, peer_principal):
        pp = peer_principal

        if self.use_signature:
            return pp.verify(self.contents_digest, self.signature)

        if len(node.replica_principals) != len(self.auth):
            return False

        return node.principal.verify(self.contents_digest,
                                     self.auth[node.index])

    @classmethod
    def from_node(cls, node, reply_to_all:int, replier:int,
                  readonly:bool, use_signature:bool,
                  command:bytes):

        extra = 0
        if readonly:
            extra |= 1
        if use_signature:
            extra |= 2

        message = cls(node.type, node.index, node.next_reqid(), extra,
                      reply_to_all, replier, command)
        message.authenticate(node, True)
        return message

    @classmethod
    def from_payloads(cls, payloads):
        try:
            [contents, auth] = rlp.decode(payloads, cls.payloads.sedes)
            [node_type, index, reqid, reply_to_all, replier,
             extra, command] = rlp.decode(contents, cls.contents_sedes)

            message = cls(node_type, index, reqid,
                          reply_to_all, replier, extra, command)

            message.contents, message.payloads = contents, payloads

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
