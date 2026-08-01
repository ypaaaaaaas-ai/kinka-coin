from Crypto.PublicKey import RSA

def generate_key_pair(key_size: int = 2048):
    key = RSA.generate(key_size)
    
    private_key_pem = key.export_key().decode("utf-8")
    
    public_key_pem = key.publickey().export_key().decode("utf-8")
    
    return private_key_pem, public_key_pem

def load_private_key(pem_string: str):
    return RSA.import_key(pem_string)

def load_public_key(pem_string: str):
    return RSA.import_key(pem_string)