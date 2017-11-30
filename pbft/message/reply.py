import hashlib
import hmac

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from . import BaseMessage

from ..types import View, Reqid, NodeType

class Reply(BaseMessage):
    contents_sedes = List([
        big_endian_int, # replier index
        big_endian_int, # timestamp(reqid)
        big_endian_int, # extra
        big_endian_int, # view
        raw, # reply digest
        raw, # reply
    ])

    payloads_sedes = List([
        raw, # contents
        raw, # auth(hmac)
    ])

    def __init__(self, sender, reqid, extra,
                 view, reply:bytes):
        """
        :sender index id of replica sending this message
        :reqid reqid from the sender
        :node_type  always be replica
        """
        self.sender = sender
        self.reqid = reqid
        self.extra = extra
        self.view = view
        self.reply = reply

        self.auth = None

    @property
    def reply_digest(self):
        d = hashlib.sha256()
        d.update(self.reply)
        return d.digest()

    @property
    def contents_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.sender).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update('{}'.format(self.extra).encode())
        d.update('{}'.format(self.view).encode())
        d.update('{}'.format(self.reply_digest).encode())
        return d.digest()

    @classmethod
    def from_node(cls, node, request, reply):

        extra = 0
        if node.type is NodeType.Client:
            extra |= 1 << 4
        
        Message = cls(node.index, request.reqid, extra, node.view, reply)

        return message

    @classmethod
    def from_payloads(cls, payloads, addr):
        try:
            [contents, auth] = rlp.decode(payloads, cls.payloads_sedes)

            [sender, reqid, extra, view, reply_digest, reply] = (
                rlp.decode(contents, cls.contents_sedes))

            message = cls(sender, reqid, extra, view, reply)
            if message.reply_digest != reply_digest:
                raise ValueError('digest error')

            message.auth = auth
            message.from_addr = addr
            return message
        except rlp.DecodingErr as exc:
            raise ValueError('decoding error: {}'.format(exc))
