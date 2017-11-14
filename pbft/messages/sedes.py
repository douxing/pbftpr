from .message import MessageType, BaseMessage
from .new_key ipmort NewKey

def serialize(message) -> bytes:
    assert isinstance(message, BaseMessage)
    assert type(message) is not BaseMessage

    return b'0x60' + message.payloads()

def deserialize(payload:bytes) -> BaseMessage:
    

