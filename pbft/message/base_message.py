from enum import IntEnum
import re

from rlp.sedes import CountableList, raw

from .types import MessageTag

class BaseMessage():

    """Prefix for our message

    :\x00 is the multibase tag for raw based
    :\x01 is the version number in unsigned varint
    :\x55 is the multicodec tag for raw based
    """
    prefix = b'\x00\x01\x55'

    infix = b'\x60' # multicoded code for rlp

    authenticators_sedes = CountableList(raw)

    def __init__(self):
        """Initialization, BaseMessage shall NOT on wire

        should ONLY be called directly when parsing a frame
        """
        pass

    def verify(self):
        raise NotImplementedError

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

    def __len__(self):
        return len(self.frame)

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
