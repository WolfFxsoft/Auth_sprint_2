"""
Hash methods
"""
import hashlib

def pass_hasher(modelpass):
    """ generate hash for password """
    pass_hash = hashlib.sha256(bytes(modelpass, encoding='utf-8'))
    res = pass_hash.hexdigest()[:64]
    return res
