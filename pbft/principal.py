import binascii

class Principal():
    def __init__(self,
                 index:int,
                 private_key = None, public_key = None,
                 ip:str = '127.0.0.1', port:int = 25600):
        self.index = index
        self.ip = ip # we send/recv by udp
        self.port = port
            
        self.private_key = private_key
        self.public_key = public_key

        # using hmac-256 for session keys
        self.outkey = None
        self.inkey = None
        self.keyts = None

    def sign(self):
        pass
