from enum import IntEnum
import re

class MessageTag(IntEnum):
    FreeMessage = 0
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

class BaseMessage():

    """Prefix for our message

    :\x00 is the multibase tag for raw based
    :\x01 is the version number in unsigned varint
    :\x55 is the multicodec tag for raw based
    """
    prefix = b'\x00\x01\x55'

    infix = b'\x60' # multicoded code for rlp

    def __init__(self):
        pass
        
    @property
    def tag(self) -> MessageTag:
        return MessageTag[type(self).__name__]

    def gen_frame(self):
        """Generate frame from tag and payloads

        this method should ONLY be called with complete message,
        which has both tag and payloads attributes
        """
        frame = (self.prefix + self.tag.to_bytes(1, byteorder='big')
                + self.infix + self.payloads)
        print(self.infix)
        print(frame[:10])
        return frame

    @classmethod
    def parse_frame(cls, frame:bytes) -> (MessageTag, bytes):
        """Convert a bytes to message

        this method will not return a complete message,
        further parse is needed
        
        :data should begin with prefix + MessageType + infix
        """
        print('message parse_frame recv: {}'.format(frame[:10]))
        if cls.prefix != frame[:3] or frame[4:5] != cls.infix:
            raise ValueError('illegal frame')
        
        return MessageTag(frame[3]), frame[5:]
