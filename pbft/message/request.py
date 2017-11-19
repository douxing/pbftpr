from ..types import Reqid
from .types import MessageTag
from .base_message import BaseMessage

class Request(BaseMessage):
    def __init__(self,
                 node_type:int, index:int,
                 reqid:Reqid):
        pass
