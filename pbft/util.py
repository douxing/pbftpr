from datetime import datetime
import math

from .types import Reqid, TaskType, Task


def utcnow_ts():
    return datetime.utcnow().timestamp()

def utcnow_reqid():
    return Reqid(math.floor(utcnow_ts() * 10**3))

def print_new_key(new_key, pp):
    if __debug__:
        print('new_key <{}:{}> updated:\n{}\n{}'.format(
            new_key.node_type, new_key.index, pp.inkey, pp.outkey))

def print_task(task):
    if __debug__:
        s = '<UTC>{} - {} '.format(str(datetime.utcnow()), task.type.name)
        if task.type is TaskType.PEER_MSG:
            (frame, addr) = task.item

            s += '{}\n'.format(addr)
            if len(frame) < 32:
                s += '(len:{}) {}\n'.format(len(frame), frame)
            else:
                s += '(len:{}) {}...{}\n'.format(
                    len(frame), frame[:16], frame[-16:])
        else:
            s += '{}\n'.format(task.item)

        print(s)
    
    
