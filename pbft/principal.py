class Principal():
    def __init__(self,
                 index:int,
                 ip:str = '127.0.0.1', port:int = 25600,
                 private_key:str, public_key:str):
        self.index = index
        self.ip = ip # we send/recv by udp
        self.port = port
        self.private_key = private_key
        self.public_key = public_key

        self.tsid = 

    def sign(self):
        pass
