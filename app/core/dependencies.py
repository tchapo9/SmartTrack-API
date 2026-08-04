from fastapi import Depends
from app.core.security import SecurityService
from app.models.user import User

async def get_current_user(current_user: User = Depends(SecurityService.get_current_user)) -> User:
    return current_user

async def get_current_active_user(current_user: User = Depends(SecurityService.get_current_active_user)) -> User:
    return current_user

async def get_current_admin_user(current_user: User = Depends(SecurityService.get_current_admin_user)) -> User:
    return current_user
