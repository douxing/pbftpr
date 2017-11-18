from enum import IntEnum
import re

from ..utils import camel_to_snake

class MessageTag(IntEnum):
    BaseMessage = 0 # FreeMessage
    Request = 1
    Reply = 2
    PrePrepare = 3
    Prepare = 4
    Commit = 5
    Checkpoint = 6
    Status = 7
    ViewChange = 8
    NewView = 9
    ViewChangeAck = 10
    NewKey = 11
    MetaData = 12
    MetaDataD = 13
    Data = 14
    Fetch = 15
    QueryStable = 16
    ReplyStable = 17

    @classmethod
    def snake_name(cls, tag):
        return _snake_names[tag]

_snake_names = { t: camel_to_snake(t.name) for t in MessageTag }

class BaseMessage():

    """Prefix for our message

    :\x00 is the multibase tag for raw based
    :\x01 is the version number in unsigned varint
    :\x55 is the multicodec tag for raw based
    """
    prefix = b'\x00\x01\x55'

    infix = b'\x60' # multicoded code for rlp

    def __init__(self):
        """Initialization, BaseMessage shall NOT on wire

        should ONLY be called directly when parsing a frame
        """
        pass

    @property
    def tag(self):
        return MessageTag[type(self).__name__]

    @property
    def frame_head(self):
        return (self.prefix
                + self.tag.to_bytes(1, byteorder='big')
                + self.infix)

    @property
    def frame(self):
        """Generate frame from tag and payloads

        this method should ONLY be called with complete message,
        which has both tag and payloads attributes
        """
        return self.frame_head + self.payloads

    @classmethod
    def parse_frame(cls, frame:bytes):
        """Convert a bytes to message

        this method will not return a complete message,
        further parse is needed
        
        :data should begin with prefix + MessageTag + infix
        """
        if cls.prefix != frame[:3] or frame[4:5] != cls.infix:
            raise ValueError('illegal frame head')
        
        tag = MessageTag(frame[3])
        payloads = frame[5:]

        if not min(MessageTag) < tag <= max(MessageTag):
            raise ValueError('illegal frame tag')
        elif not payloads:
            raise ValueError('illegal frame payloads')

        return tag, payloads
