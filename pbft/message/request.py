import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Reqid, Configuration as conf
from .message_tag import MessageTag
from .base_message import BaseMessage

class Request(BaseMessage):

    content_sedes = List([
        big_endian_int, # sender index
        big_endian_int, # timestamp(reqid)
        big_endian_int, # extra bitmap
        big_endian_int, # full replier
        raw, # command or command_digest
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(authenticators or signature)
             # maybe empty(b'') if content contains command_digest
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
        super().__init__();

        self.sender = sender
        self.reqid = reqid
        self.extra = extra
        self.full_replier = full_replier
        self.reply_will_full = False

        self.command = command
        self._command_digest = None

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
        """compute digest for command"""
        if self.command:
            d = hashlib.sha256()
            # dx: i am going to use the data instead of hahs
            # so I am commenting them out.
            # d.update('{}'.format(self.sender).encode())    # useless
            # d.update('{}'.format(self.reqid).encode())     # useless
            d.update(self.command)                           # useful
            return d.digest()

        return self._command_digest

    @property.setter
    def command_digest(self, new_command_digest):
        if not self.command:
            self._command_digest = new_command_digest

    @property
    def consensus_digest(self):
        d = hashlib.sha256()
        if self.sender_type is 'Client':
            d.update('{}'.format(1).encode())
        else:
            d.update('{}'.format(0).encode())
        d.update('{}'.format(self.sender).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update(self.command_digest)
        return d.digest()

    @property
    def content_digest(self):
        d = hashlib.sha256()
        if self.sender_type is 'Client':
            d.update('{}'.format(1).encode())
        else:
            d.update('{}'.format(0).encode())
        d.update('{}'.format(self.sender).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update('{}'.format(self.extra).encode())
        d.update('{}'.format(self.full_replier).encode())
        d.update(self.command_digest) # includes command and len(command)
        return d.digest()

    def gen_payload(self, node):
        self.content = rlp.encode([
            self.sender, self.reqid, self.extra,
            self.full_replier, self.command,
        ], self.content_sedes)

        self.authenticate(node)
        self.payload = rlp.encode([self.content, self.raw_auth],
                                  self.payload_sedes)

    def change_by_primary(self, request, primary):
        assert self.verified

        changed = False
        if self.extra != request.extra:
            self.extra = request.extra
            changed = True
        if self.full_replier != request.full_replier:
            self.full_replier = request.full_replier
            changed = True
        if self.auth != request.auth:
            self.auth = request.auth
            changed = True # re-authenticated

        self.reply_with_full = (self.reply_with_full
                                or self.reply_from_all
                                or self.full_replier == primary.index)

        if changed:
            self.gen_payload()

       return changed

    def change_by_backup(self, request, backup):
        assert request.verified # only allow verified request

        if not self.command:
            self.command = request.command
        assert self.command == request.command

        changed = False
        if self.extra != request.extra:
            self.extra = request.extra
            changed = True
        if self.full_replier != request.full_replier:
            self.full_replier = request.full_replier
            changed = True
        if self.auth != request.auth:
            self.auth = request.auth
            changed = True # re-authenticated

        self.reply_with_full = (self.reply_with_full
                                or self.reply_from_all
                                or self.full_replier == backup.index)

        self.verified = True # if was False, updated by verified reuqest

        if changed:
            self.gen_payload()

        return changed

    def authenticate(self, node):
        if self.use_signature:
            self.auth = node.principal.sign(self.content_digest)
        else:
            self.auth = node.gen_authenticators(self.content_digest)

        return self.auth

    def verify(self, node, peer_principal):
        pp = peer_principal

        if self.verified or not self.auth:
            pass # already verified or no auth to verify
        elif self.use_signature:
            self.verified = pp.verify(self.content_digest, self.auth)
        else:
            if len(node.replica_principals) != len(self.auth):
                self.verifed = False
            else:
                # for request, we use 'out' key for the authentication
                assert pp.index == self.sender
                self.verified = (pp.gen_hmac('out', self.content_digest)
                                 == self.auth[self.sender])

        return self.verified

    @property
    def payload_in_pre_prepare(self):
        if len(self.command) <= conf.pre_prepare_big_request_thresh:
            return self.payload

        content = rlp.encode([
            self.sender, self.reqid, self.extra,
            self.full_replier, self.command_digest
        ], message.content_sedes)

        payload = rlp.encode([content, b''], message.payload_sedes)

        return payload


    @classmethod
    def from_client(cls, node,
                  readonly:bool, use_signature:bool, reply_from_all:bool,
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
        message.gen_payload()

        return message

    @classmethod
    def from_payload(cls, payload, addr, node):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)
            [sender, reqid, extra, full_replier, extra, command] = (
                rlp.decode(content, cls.content_sedes))

            if not auth:
                # this should be a request inside of a pre_prepare
                # it has no auth attached, get the full request form client
                message = cls(sender, reqid, extra, full_replier, None)
                message.command_digest = command
            else:
                # full request
                message = cls(sender, reqid, extra, full_replier, command)
                if message.use_signature:
                    message.auth = auth
                else:
                    message.auth = rlp.decode(auth, cls.authenticators_sedes)

            message.content = content
            message.payload = payload
            
            if (message.reply_from_all
                or message.full_replier == node.index):
                message.reply_with_full = True

            message.from_addr = addr

            return message
        except rlp.DecodingError as exc:
            raise ValueError('decoding error: {}'.format(exc))
