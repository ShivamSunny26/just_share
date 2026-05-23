import bcrypt


# 1. Password Security (Salting & Hashing using Bcrypt)

def hash_password(password: str) -> str:
    """Generate a secure salt and hashed the password"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str)-> bool:
    """Verifies a plain password against its database hash."""
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

