from Crypto.PublicKey import RSA


def generate_key_pair(key_size: int = 2048):
    key = RSA.generate(key_size)
    
    get_private_key = key.export_key().decode("utf-8")
    
    get_public_key = key.publickey().export_key().decode("utf-8")
    
    return get_private_key, get_public_key

def load_private_key(pem_string: str):
    return RSA.import_key(pem_string)

def load_public_key(pem_string: str):
    return RSA.import_key(pem_string)
