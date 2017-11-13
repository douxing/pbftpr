from ..types import Reqid
from .message import MessageTag, Message

class NewKey(Message):
    def __init__(self,
                 reqid:Reqid, index:int,
                 *args, **kwargs):
        """Session key
        """
        self.reqid = reqid
        self.index = index
        
        super().__init__(*args, **kwargs)

