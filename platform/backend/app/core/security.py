from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models import Role, User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def hash_password(value: str) -> str: return pwd.hash(value)
def verify_password(value: str, hashed: str) -> bool: return pwd.verify(value, hashed)
def make_token(user: User) -> str:
    payload={"sub":str(user.id),"role":user.role.value,"exp":datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)}
    return jwt.encode(payload,settings.secret_key,algorithm=ALGORITHM)

def current_user(request: Request, db: Session=Depends(get_db)) -> User:
    token=request.cookies.get("utn_session")
    auth=request.headers.get("Authorization","")
    if not token and auth.startswith("Bearer "): token=auth[7:]
    try: user_id=int(jwt.decode(token or "",settings.secret_key,algorithms=[ALGORITHM])["sub"])
    except (JWTError,KeyError,ValueError): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication required")
    user=db.get(User,user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401,detail="Account is inactive")
    return user

def allow(*roles: Role):
    def check(user: User=Depends(current_user)):
        if user.role not in roles: raise HTTPException(status_code=403,detail="You do not have permission for this action")
        return user
    return check
