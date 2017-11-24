from . import BaseMessage

from ..types import View, Reqid

class Reply(BaseMessage):
    def __init__(self,
                 view, reqid, replicaid):
        self.view = view
        self.reqid = reqid
        self.replicaid = replicaid
        self.answer = None

