from .base_message import BaseMessage

from ..types import NodeType
from .types import big_request_thresh

class PrePrepare(BaseMessage):

    contents_sedes = List([
        big_endian_int, # view
        big_endian_int, # seqno
        # requests, with sha256(0x12) or payloads(0x60)
        CountableList([raw, raw]),
    ])

    payloads_sedes = List([
        raw, # contents
        raw, # auth(signature)
    ])

    def __init__(self, view, seqno, requests):
        self.view = view
        self.seqno = seqno
        self.requests = requests

    @classmethod
    def from_node(cls, node):
        requests = [] # or sha256
        for r in node.requests:
            if r.in_pre_prepare:
                continue

            if len(r) < big_request_thresh:
                requests.append((0x60, r.payloads))
            else:
                requests.append((0x12, r.contents_digest))
            r.in_pre_prepare = True

        message = cls(node.view, node.seqno, requests)
        return message

    @classmethod
    def from_payloads(cls, payloads):
        pass
