from 鍵管理 import generate,get_public_key,get_private_key
class 財布:
    def __init__(self):
        self.public_key = None
        self.private_key = None

    def generate(self):
        鍵管理.generate()
        self.public_key = 鍵管理.get_public_key()
        self.private_key = 鍵管理.get_private_key()

    def get_public_key(self):
        return self.public_key

    def get_private_key(self):
        return self.private_key
        
        