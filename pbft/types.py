from enum import IntEnum
from typing import NewType

Reqid = NewType('Reqid', int)
Seqno = NewType('Seqno', int)
View  = NewType('View',  Seqno)
