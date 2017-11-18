import secrets

import rsa

from .types import Reqid

class Principal():
    
    hash_method = 'SHA-256'

    hmac_nounce_length = 32
    zero_hmac_nounce = bytes(hmac_nounce_length)

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
        self.outkey = self.zero_hmac_nounce
        self.outkey_reqid = Reqid(0) # outkey timestamp
        self.inkey = self.zero_hmac_nounce

    @property
    def addr(self):
        return (self.ip, self.port)

    def sign(self, message:bytes) -> bytes:
        print(self.private_key)
        print(self.public_key)

        return rsa.sign(message, self.private_key, self.hash_method)

    def verify(self, message:bytes, signature) -> bool:
        return rsa.verify(message, signature, self.public_key)

    def encrypt(self, message:bytes) -> bytes:
        return rsa.encrypt(message, self.public_key)

    def decrypt(self, message:bytes) -> bytes:
        return rsa.decrypt(message, self.private_key)

    def gen_inkey(self):
        self.inkey = secrets.token_bytes(self.hmac_nounce_length)
        return self.inkey
