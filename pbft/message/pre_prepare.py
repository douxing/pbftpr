import hashlib

from .base_message import BaseMessage

from ..basic import Configuration as conf

class PrePrepare(BaseMessage):

    content_sedes = List([
        big_endian_int, # view
        big_endian_int, # seqno
        # requests, with sha256(0x12...) or payload(0x60...)
        CountableList(raw),
    ])

    payload_sedes = List([
        raw, # content
        raw, # auth(signature)
    ])

    def __init__(self, view, seqno, requests, non_det_choices):
        self.view = view
        self.seqno = seqno
        self.requests = requests
        self.non_det_choices = non_det_choices

    def requests_digest(self):
        """for requests, it only calculate the digest w/o auth
        and followed by the non_det_choices
        """
        d = hashlib.sha256()
        for r in self.requests:
            d.update(r.)
        return d.digest()

    def content_digest(self):
        d = hashlib.sha256()
        d.update('{}'.format(self.view).encode())
        d.update('{}'.format(self.seqno).encode())
        for r in self.requests:
            d.update(r)
        d.update(self.non_det_choices)
        return d.digest()

    @classmethod
    def from_node(cls, node):
        requests = [] # request payload or sha256
        for r in node.requests:
            if r.in_pre_prepare:
                continue

            requests.append(r)
            r.in_pre_prepare = True

            if len(requests) >= conf.request_in_pre_prepare:
                break
            
            # if len(r) < conf.request_in_pre_prepare:
            #     requests.append(b'\x60' + r.payload)
            # else:
            #     requests.append(b'\x12' + r.content_digest)

        non_det_choices = b'' # TODO non deterministic choices

        message = cls(node.view, node.seqno, requests, non_det_choices)
        return message

    @classmethod
    def from_payload(cls, payload):
        pass
