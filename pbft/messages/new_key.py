import secrets

from rlp.sedes import List, CountableList, big_endian_int, raw

from ..types import Reqid
from .message import MessageTag, BaseMessage

class NewKey(BaseMessage):

    contents_sedes = List([
        big_endian_int, # sender index
        CountableList(raw), # [k(j, i)]
        big_endian_int, # timestamp
    ])

    payloads_sedes = List([
        raw, # contents
        raw, # signature
    ])

    def __init__(self,
                 reqid:Reqid, index:int,
                 keys = [],
                 *args, **kwargs):
        """Session key
        """
        self.reqid = reqid
        self.index = index
        self.hmac_keys = []
        for i, key in enumerate(keys):
            if i == self.index:
                self.hmac_keys.append(b'') # ignore key with self
                continue

            self.hmac_keys.append(key)

        self.signature = None
        
        super().__init__(*args, **kwargs)

    def contents(self) -> bytes:
        

    def payloads(self) -> bytes:
        pass
