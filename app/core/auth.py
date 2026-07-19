from passlib.context import CryptContext
from jose import JWTError,jwt
from app.core.config import access
from datetime import datetime,timedelta,timezone

pwd=CryptContext(schemes=["bcrypt"], deprecated="auto")
YOUR_SECRET_CODE=access.your_secret_code
ALGORITHM=access.algorithm

def hash_pw(password:str):
    return pwd.hash(password)

def verify_pw(password:str,hashed_password:str):
    return pwd.verify(password,hashed_password)

def create_token(data:dict,minutes:int):
    to_encode=data.copy()
    expiry=datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp":expiry})
    return jwt.encode(to_encode,YOUR_SECRET_CODE,algorithm=ALGORITHM)

def decode_token(token:str):
    try:
        payload= jwt.decode(token,YOUR_SECRET_CODE,algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None