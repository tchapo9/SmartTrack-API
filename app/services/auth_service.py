from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, PasswordChange
from app.core.security import SecurityService
from app.core.exceptions import NotFoundError, ConflictError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=SecurityService.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not SecurityService.verify_password(password, user.password_hash):
            return None
        return user

    async def refresh_token(self, refresh_token: str) -> User:
        payload = SecurityService.verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ConflictError("Invalid refresh token")
        user_id = payload.get("sub")
        if user_id is None:
            raise ConflictError("Invalid refresh token")

        user = await self.db.get(User, int(user_id))
        if not user:
            raise NotFoundError("User not found")
        return user

    async def change_password(self, user_id: int, password_data: PasswordChange) -> None:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        if not SecurityService.verify_password(password_data.current_password, user.password_hash):
            raise ConflictError("Current password is invalid")
        user.password_hash = SecurityService.get_password_hash(password_data.new_password)
        await self.db.commit()
