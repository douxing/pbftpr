from .types import Reqid, Seqno, View

class Node():
    def __init__(self):
        self._n = 0
        self._f = 0
        self._principals = []

        self._view = View(0)
        self._primary = 0 # id

        self.ip = '0.0.0.0'
        self.port = 0

    @property
    def view(self) -> View:
        """Get the current view."""
        return self._view
