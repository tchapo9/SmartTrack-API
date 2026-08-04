from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.core.exceptions import UnauthorizedError, ForbiddenError

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class SecurityService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise UnauthorizedError("Invalid token")

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise UnauthorizedError("Invalid token")
        except JWTError:
            raise UnauthorizedError("Invalid token")
        
        user = await db.get(User, int(user_id))
        if user is None:
            raise UnauthorizedError("User not found")
        
        return user

    @staticmethod
    async def get_current_active_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        current_user = await SecurityService.get_current_user(token=token, db=db)
        if not current_user.is_active:
            raise ForbiddenError("Inactive user")
        return current_user

    @staticmethod
    async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Admin privileges required")
        return current_user