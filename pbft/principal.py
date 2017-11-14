import rsa

class Principal():
    
    hash_method = 'SHA-256'

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
        self.outkeyts = 0 # outkey timestamp
        self.inkey = None

    def sign(self, message:bytes) -> bytes:
        return rsa.sign(message, self.private_key, self.hash_method)

    def verify(self, message:bytes, signature) -> bool:
        return rsa.verify(message, signature, self.hash_method)

    def encrypt(self, message:bytes) -> bytes:
        return rsa.encrypt(message, self.public_key)

    def decrypt(self, message:bytes) -> bytes:
        return rsa.encrypt(message, self.private_key)
