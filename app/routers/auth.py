from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.core.security import SecurityService
from app.core.exceptions import UnauthorizedError, ConflictError
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, RefreshToken, 
    UserResponse, PasswordChange
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    auth_service = AuthService(db)
    
    # Check if user exists
    existing_user = await auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise ConflictError("Email already registered")
    
    existing_username = await auth_service.get_user_by_username(user_data.username)
    if existing_username:
        raise ConflictError("Username already taken")
    
    # Create user
    user = await auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login user and return JWT tokens"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise UnauthorizedError("Invalid credentials")
    
    # Generate tokens
    access_token = SecurityService.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = SecurityService.create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60  # 30 minutes in seconds
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    user = await auth_service.refresh_token(refresh_data.refresh_token)
    
    access_token = SecurityService.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_data.refresh_token,
        "token_type": "bearer",
        "expires_in": 30 * 60
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: UserResponse = Depends(SecurityService.get_current_active_user)
):
    """Get current user profile"""
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(SecurityService.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    await auth_service.change_password(current_user.id, password_data)
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user = Depends(SecurityService.get_current_active_user)
):
    """Logout user (client should discard tokens)"""
    return {"message": "Logged out successfully"}