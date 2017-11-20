import hashlib

import rlp
from rlp.sedes import List, CountableList, big_endian_int, raw

from ..types import Reqid
from .types import MessageTag
from .base_message import BaseMessage

class Request(BaseMessage):

    contents_sedes = List([
        big_endian_int, # sender type
        big_endian_int, # sender index
        
        big_endian_int, # timestamp        
    ])

    payloads_sedes = List([
        raw, # 
        raw,
    ])
    

    def __init__(self,
                 node_type:int, index:int, 
                 reqid:Reqid, replier:int,
                 command:bytes,
                 authenticators):
        """

        :command
        :authenticators may use signature instead
        """

        self.node_type = node_type
        self.index = index
        self.reqid = reqid
        self.replier = replier
        self.command = command
        self.authenticators = authenticators
        
        

    @classmethod
    def from_principal(self,
                       node_type:int, index:int, reqid:Reqid,
                       principal, replica_principals):

        d = hashlib.sha256()
        d.update('{}'.format(node_type).encode())
        d.update(command)

        
        
        
