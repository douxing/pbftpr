import collections

from .types import Seqno

class BaseLog():
    def __init__(self, capacity:int, head:Seqno):
        """
        :capacity: should be a power of 2
        """
        self.head = head
        self.capacity = capacity
        self.items = []

    def truncate(self. new_head):
        if new_head <= self.head:
            return

        for i in range(min(self.capacity, new_head - self.head)):
            index = head + i & self.capacity - 1
            self.items[index].init(Seqno(new_head + index))

        self.head = new_head

    def __getitem__(self, key:int):
        if key < self.head or key >= self.head + self.capacity:
            return None

        index = key & self.capacity - 1
        return self.items[index]

    def __len__(self):
        return self._capacity

class PrepareCertificate():
    def __init__(self, plog):
        self.plog = plog
        self.prepares = collections.OrderedDict() # replica index -> prepare
        self.prepare_count = dict() # pre_prepare digest -> count of prepare
        self.commits = collections.OrderedDict()  # replica index -> commit

    def init(self, seqno:Seqno):
        self.seqno = seqno

        if self.pre_prepare and self.pre_prepare.requests:
            for r in pre_prepare.requests:
                del self.plog.requests[(request.sender_type,
                                       request.sender,
                                       request.reqid)]

        self.pre_prepare = None
        self.prepares.clear()
        self.prepare_count.clear()
        self.commits.clear()
        
    @property
    def my_prepare(self):
        return self.prepares[self.plog.replica.index]

    @property
    def my_commit(self):
        return self.commits[self.plog.replica.index]

    def add_pre_prepare(self, pre_prepare):
        for i, r in enumerate(pre_prepare.requests):
            r.seqno = self.seqno
            r.in_pre_prepare_index = i
            assert not self.plog.requests[(r.sender_type, r.sender, r.reqid)]
            self.plog.requests[(r.sender_type, r.sender, r.reqid)] = r

        self.pre_prepare = pre_prepare

    @property
    def is_pre_prepared(self):
        if (self.pre_prepare
            and (self.pre_prepare.mine
                 or self.my_prepare)):
            return True

        return False

    def add_prepare(self, prepare):
        if not self.prepares.get(prepare.sender):
            self.prepares[prepeare.sender] = prepare
            count = self.prepare_count.get(prepare.consensus_digest, 0)
            self.prepare_count[prepare.consensus_digest] = count + 1
            return True

        return False

    @property
    def is_prepared(self):
        if self.is_pre_prepared:
            c = self.prepare_count.get(pre_prepare.consensus_digest, 0)
            return c >= 2 * self.plog.replica.f

        return False

    def add_commit(self, commit):
        if not self.commits.get(commit.sender):
            self.commits[commit.sender] = commit
            return True

        return False

    @property
    def is_committed(self):
        if self.is_prepared:
            # include mine
            return len(self.commits) > self.plog.replica.f * 2

        return False
                
class PrepareCertificateLog(BaseLog):
    def __init__(self, replica, capacity, head):
        super().__init__(self, capacity,  head)

        self.replica = replica

        # this is the index of requests in all pre_prepares
        # (sender_type, sender_index, reqid) => request
        self.requests = dict()

        # init with proper seqno
        head_index = head & capacity - 1
        for i in range(head_index):
            pcert = PrepareCertificate(self)
            pcert.init(head + capacity - head_index + i)
            self.items.append(pcert)

        for i in range(self.capacity - head_index):
            pcert = PrepareCertificate(self)
            pcert.init(head + i)
            self.items.append(pcert)

    def get_request(self, request):
        return self.requests.get((request.sender_type,
                                  request.sender,
                                  request.reqid))
