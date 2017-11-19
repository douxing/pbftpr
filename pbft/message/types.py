from enum import IntEnum
import re

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
        return cls.snake_names[tag]

    def const_name(cls, tag):
        return cls.const_names[tag]

def camel_to_snake(name):
    return re.sub('(.)([A-Z])', r'\1_\2', name).lower()

MessageTag.snake_names  = {
    t: camel_to_snake(t.name) for t in MessageTag
}

MessageTag.const_names = {
    t: camel_to_snake(t.name).upper() for t in MessageTag
}

