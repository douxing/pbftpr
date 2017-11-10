from .principal import Principal
from .node import Node

class Client(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def principal(self) -> Principal:
        """Get principal of this node."""
        return self.client_principals[self.index]
