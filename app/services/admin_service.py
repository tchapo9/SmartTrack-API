from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.user import User
from app.models.device import Device
from app.models.alert import Alert
from app.core.exceptions import NotFoundError


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self) -> List[User]:
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()

    async def get_user(self, user_id: int) -> User:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def list_devices(self) -> List[Device]:
        result = await self.db.execute(select(Device).order_by(Device.created_at.desc()))
        return result.scalars().all()

    async def list_alerts(self) -> List[Alert]:
        result = await self.db.execute(select(Alert).order_by(Alert.created_at.desc()))
        return result.scalars().all()

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user(user_id)
        await self.db.delete(user)
        await self.db.commit()
