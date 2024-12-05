# shortuuid.py
from datetime import datetime
from hashids import Hashids

UUID_SALT = "Y_wjhVQ4:RRs"
ALPHABETS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ23456789"

hashids = Hashids(salt=UUID_SALT, min_length=9, alphabet=ALPHABETS)


def generate(prefix=None, max_length=0):
    """
    Generate url-friendly uids based on current unix UTC timestamp.

    Ref: http://hashids.org/python/

    """
    t = datetime.utcnow().timestamp() * 10000
    if prefix:
        result = '{}{}'.format(prefix, hashids.encode(int(t)))
    else:
        result = hashids.encode(int(t))

    if max_length:
        result = result[:max_length]

    return result
