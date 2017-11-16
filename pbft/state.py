from .log import Log
from .partition import Partition

class State():
    def __init__(self):

        self.total_size = 0

        self.partition_tree =  []
        # initialize partition tree
        for l in range(Partition.level_count):
            ps = [Partition(level = l, index = i,
                            last_mod_checkpoint = 0)
                  for i in range(Partition.children_count ** l)]
            self.partition_tree.append(ps)

        self.last_stable_checkpoint = Seqno(0)
        # TODO: self.checkpoint_log = []

        self.is_checking = False
        self.is_fetching = False
    
    def compute_full_digest(self):
        """Initialize state
        """

        # handle leaves first
        for p in self.partition_tree[-1]:
            p.digest = p.compute_digest(p.block)

        # handle non-leaves
        for psi in range(len(self.partition_tree) - 2, -1, -1):
            for pi, p in enumerate(self.partition_tree[psi]):
                assert pi == p.index

                sums = b''
                cbi = pi * Partition.children_count
                cei = cbi + Partition.children_count
                for c in self.partition_tree[psi + 1][cbi:cei]:
                    sums += c.digest
                p.digest = p.compute_digest(sums)

        # TODO: update self.checkpint_log

    def update_partition_tree(self, n:Seqno):
        pass
        
    def checkpoint(self):
        pass
