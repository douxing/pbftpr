import secrets
import hmac
import traceback

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
        try:
            return rsa.sign(message, self.private_key, self.hash_method)
        except:
            traceback.print_exc()

        return None

    def verify(self, message:bytes, signature) -> bool:
        try:
            rsa.verify(message, signature, self.public_key)
            return True
        except:
            traceback.print_exc()

        return False
            

    def encrypt(self, message:bytes) -> bytes:
        try:
            return rsa.encrypt(message, self.public_key)
        except:
            traceback.print_exc()

        return None

    def decrypt(self, message:bytes) -> bytes:
        try:
            return rsa.decrypt(message, self.private_key)
        except:
            traceback.print_exc()

        return None

    def gen_inkey(self):
        self.inkey = secrets.token_bytes(self.hmac_nounce_length)
        return self.inkey

    def gen_hmac(self, inout, source):
        """Generate hmac for the input

        nonce is NOT used, I believe that hmac-sha256 is secure enough
        """
        assert inout == 'in' or inout == 'out'

        if inout == 'in':
            key = self.inkey
        elif inout == 'out':
            key = self.outkey

        return hmac.new(key, source, digestmod='SHA256').digest()
        
