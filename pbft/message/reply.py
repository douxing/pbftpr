import hashlib
import hmac

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from . import BaseMessage

from ..basic import View, Reqid

class Reply(BaseMessage):
    content_sedes = List([
        big_endian_int, # view
        big_endian_int, # timestamp(reqid)
        big_endian_int, # extra
        big_endian_int, # requestor index
        big_endian_int, # replier index
        raw, # result or digest
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(hmac)
    ])

    def __init__(self, view, reqid,  extra,
                 sender, replier, result:bytes):
        """
        :sender index id of replica sending this message
        :reqid reqid from the sender
        :node_type  always be replica
        """
        super().__init__()

        self.view = view
        self.reqid = reqid
        self.extra = extra
        self.sender = sender # sender of request
        self.replier = replier
        self.result = result

        self.requestor = None # principal

        self.content = None
        self.auth = None
        self.payload = None

    @property
    def reply_digest(self):
        d = hashlib.sha256()
        d.update(self.reply)
        return d.digest()

    @property
    def content_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.view).encode())
        d.update('{}'.format(self.reqid).encode())
        d.update('{}'.format(self.extra).encode())
        d.update('{}'.format(self.sender).encode())
        d.update('{}'.format(self.replier).encode())
        d.update('{}'.format(self.reply_digest).encode())
        return d.digest()

    @classmethod
    def from_node(cls, node, request, reply):

        extra = 0
        if node.type is 'Client':
            extra |= 1 << 4

        Message = cls(node.index, request.reqid, extra, node.view, reply)

        return message

    @classmethod
    def from_payload(cls, payload, addr, _node):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)

            [sender, reqid, extra, view, reply_digest, reply] = (
                rlp.decode(content, cls.content_sedes))

            message = cls(sender, reqid, extra, view, reply)
            if message.reply_digest != reply_digest:
                raise ValueError('digest error')

            message.auth = auth
            message.from_addr = addr
            return message
        except rlp.DecodingErr as exc:
            raise ValueError('decoding error: {}'.format(exc))
