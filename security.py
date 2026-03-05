from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # bcrypt safe limit
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password = password[:72]
    return pwd_context.hash(password)