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
        self.digest_to_prepares = dict() # digest -> set(Prepare)
        self.digest_to_commits = dict() # digest -> set(Commit)

    def init(self, seqno:Seqno):
        self.seqno = seqno

        if self.pre_prepare and self.pre_prepare.requests:
            for r in pre_prepare.requests:
                del self.plog.requests[(request.sender_type,
                                       request.sender,
                                       request.reqid)]

        self.pre_prepare = None
        self.prepares = [None] * self.replica.n # replica index -> prepares
        self.digest_to_prepares.clear()
        self.commits = [None] * self.replica.n # replica index -> commits
        self.digest_to_commits.clear()

    @property
    def my_prepare(self):
        return self.prepares[self.plog.replica.index]

    def add_pre_prepare(self, pre_prepare, mine:bool=False):
        pre_prepare.mine = mine
        for i, r in enumerate(pre_prepare.requests):
            r.seqno = self.seqno
            r.in_pre_prepare_index = i
            assert not self.plog.requests[(r.sender_type, r.sender, r.reqid)]
            self.plog.requests[(r.sender_type, r.sender, r.reqid)] = r

        self.pre_prepare = pre_prepare

    def is_pre_prepared(self):
        if (self.pre_prepare
            and (self.pre_prepare.mine
                 or self.my_prepare)):
            return True

        return False

    def add_prepare(self, prepare):
        pass

    def is_prepared(self):
        if self.pre_prepare:
            if self.pre_prepare.mine:
                return len(self.prepares) >= 2 * self.plog.replica.f
            elif self.my_prepare:
                return len(self.prepares) >= 2 * self.plog.replica.f - 1

        return False

    def add_prepare(self, prepare, mine:bool=False):
        if mine:
            self.my_prepare = prepare
        else:
            self.prepares
    

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
