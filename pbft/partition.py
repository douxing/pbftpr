import hashlib

from .types import Seqno

class Partition():

    """Page size"""
    block_size = 4096

    """Default block content"""
    zero_block = bytes(block_size)

    """Default number of children for partitions"""
    children_count = 2 << 8 # 256

    """Default number of levels in partition tree"""
    level_count = 3

    def __init__(self,
                 level:int, index:int,
                 last_mod_checkpoint:Seqno):

        """Partition

        last_mod_checkpoint: checkpoint sequence number of last modification
        """
        self.level = level
        self.index = index
        self.last_mod_checkpoint = last_mod_checkpoint
        self.digest = None

        # only leaf partition have blocks
        self._block = None

    @property
    def block(self):
        return self._block if self._block else Partition.zero_block

    @block.setter
    def block(self, value:bytes):
        self._block = value

    def compute_digest(self, data:bytes):
        assert self.level < Partition.level_count
        assert self.index < Partition.children_count ** self.level

        d = hashlib.sha256()
        # dx: intentionally use a simple encoding method
        d.update('{}'.format(self.index).encode())
        d.update('{}'.format(self.last_mod_seqno).encode())
        d.update(data)
        return d.digest()
