from enum import IntEnum
import re

from rlp.sedes import CountableList, raw

from .message_tag import MessageTag

class BaseMessage():

    """Prefix for our message

    :\x55 is the multicodec tag for raw based
    :\x01 is the version number in unsigned varint
    """
    prefix = b'\x55\x01'

    authenticators_sedes = CountableList(raw)

    def __init__(self):
        """Initialization, BaseMessage shall NOT on wire

        should ONLY be called directly when parsing a frame
        """
        self.verified = False

    def verify(self):
        raise NotImplementedError

    @property
    def tag(self):
        return MessageTag[type(self).__name__]

    @property
    def sender_type:
        if hasattr(self, 'extra'):
            return 'Replica' if (self.extra >> 4) & 1) else 'Client'
        else:
            return 'Replica'

    @property
    def frame_head(self):
        return (self.prefix
                + self.tag.to_bytes(1, byteorder='big'))

    @property
    def frame(self):
        """Generate frame from tag and payload

        this method should ONLY be called with complete message,
        which has both tag and payload attributes
        """
        return self.frame_head + self.payload

    def __len__(self):
        """Total length of this frame
        """
        # dx: I think this is more efficient than:
        # return len(self.frame)
        return len(self.frame_head) + len(self.payload)

    @classmethod
    def parse_frame(cls, frame:bytes):
        """Convert a bytes to message

        this method will not return a complete message,
        further parse is needed
        
        :data should begin with prefix + MessageTag + infix
        """
        if cls.prefix != frame[:2]
            raise ValueError('illegal frame head')
        
        tag = MessageTag(frame[2])
        payload = frame[3:]

        if not min(MessageTag) < tag <= max(MessageTag):
            raise ValueError('illegal frame tag')
        elif not payload:
            raise ValueError('illegal frame payload')

        return tag, payload
