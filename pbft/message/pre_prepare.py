import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..basic import Configuration as conf
from .base_message import BaseMessage
from .request import Request

class PrePrepare(BaseMessage):

    content_sedes = List([
        big_endian_int, # view
        big_endian_int, # seqno
        big_endian_int, # extra
        # requests, with sha256(b'\x12...') or payload('\x60...')
        CountableList(raw),
        raw, # non_det_choices
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(signature)
    ])

    def __init__(self, view, seqno, extra,
                 requests, non_det_choices):
        super().__init__()
        
        self.view = view
        self.seqno = seqno
        self.extra = extra
        self.requests = requests
        self.non_det_choices = non_det_choices

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

    @property
    def consensus_digest(self):
        """Used to make sure that primary did NOT tamper the requests
        including all request.consensus_digest and non_det_choices
        """
        d = hashlib.sha256()
        for r in self.requests:
            d.update(r.consensus_digest)
        d.update(self.non_det_choices)

        return d.digest()

    @property
    def content_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.view).encode())
        d.update('{}'.format(self.seqno).encode())
        d.update('{}'.format(self.extra).encode())
        for r in self.requests:
            d.update(r.content_digest)
        d.update(self.non_det_choices)
        return d.digest()

    def verified_requests_count(self, node):
        count = 0
        for r in self.requests:
            if r.verified:
                count += 1
        return count

    def gen_payload(self, primary):
        raw_requests = [r.payload_in_pre_prepare for r in self.requests]
        self.content = rlp.encode([self.view, self.seqno,
                                   self.extra, raw_requests,
                                   self.non_det_choices],
                                  cls.content_sedes)

        self.authenticate(primary)
        self.payload = rlp.encode([self,content, self.raw_auth],
                                  cls.payload_sedes)

    @classmethod
    def from_primary(cls, primary, use_signature:bool):
        extra = 0
        if use_signature:
            extra |= 2

        non_det_choices = b'' # TODO: non deterministic choices
        message = cls(primary.view, primary.seqno, extra,
                      None, non_det_choices)

        requests = [] # request payload
        for rs in primary.rw_requests:
            if rs and rs[-1].pre_prepare_candidate:
                r = rs.pop(-1)
                requests.append(r)

            if len(requests) >= conf.request_in_pre_prepare:
                break

        message.requests = requests
        message.gen_payload(primary)

        return message

    @classmethod
    def from_payload(cls, payload, addr, node):
        try:
            [content, auth] = rlp.decode(payload, cls.payload_sedes)
            [view, seqno, extra, requests, non_det_choices] = rlp.decode(
                content, cls.content_sedes)

            for i, r in enumerate(requests):
                requests[i] = Request.from_payload(r, addr, node)
            
            message = cls(view, seqno, extra, requests, non_det_choices)

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
