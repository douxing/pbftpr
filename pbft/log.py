from .types import Seqno

class BaseLog():
    def __init__(self, cls, capacity:int, head:Seqno):
        """
        :capacity: should be a power of 2
        """
        self.cls = cls
        self.head = head
        self.capacity = capacity
        self.logs = []

    def truncate(self. new_head):
        if new_head <= self.head:
            return

        for i in range(min(self.capacity, new_head - self.head)):
            index = head + i & self.capacity - 1
            self.logs[index] = None

        self.head = new_head

    def __getitem__(self, key:int):
        if key < self.head or key >= self.head + self.capacity:
            raise IndexError()
        
        index = key & self.capacity - 1
        if not self.logs[index]:
            self.logs[index] = cls()

        return self.logs[index]

    def __len__(self):
        return self._capacity

class PrepareCertificate():
    def __init__(self, log):
        self.log = log
        self.prepares = dict()
        self.commits = dict()
        self.clear()

    def clear(self):
        self.my_pre_prepare = None
        self.pre_prepare = None
        self.my_prepare = None
        self.prepares.clear() # digest -> Prepare
        self.my_commit = None
        self.commits.clear() # digest -> Commit

    def is_pre_prepared(self):
        if (self.my_pre_prepare
            or (self.pre_prepare and self.my_prepare)):
            return True

        return False

    def is_prepared(self):
        if self.my_pre_prepare:
            return len(self.prepares) >= 2 * self.log.f
        elif self.pre_prepare and self.my_prepare:
            return len(self.prepares) >= 2 * self.log.f - 1

        return False

class PrepareCertificateLog(BaseLog):
    def __init__(self, f, capacity, head):
        self.f = f
        super(self, PrepareCertificateLog).__init__(self, capacity,  head)

        for _ in range(self.capacity):
            self.logs.append(PrepareCertificate(self))

