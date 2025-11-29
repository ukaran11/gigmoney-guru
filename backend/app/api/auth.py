"""
GigMoney Guru - Authentication API
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import UserRegister, UserLogin, Token
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user from JWT token."""
    token = credentials.credentials
    token_data = AuthService.decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await AuthService.get_user_by_id(token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


@router.post("/register", response_model=Token)
async def register(data: UserRegister):
    """Register a new user."""
    try:
        user = await AuthService.register_user(
            name=data.name,
            phone=data.phone,
            password=data.password,
            email=data.email,
            city=data.city,
        )
        
        # Create access token
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "phone": user.phone}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            name=user.name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Catch any bcrypt or other errors
        error_msg = str(e)
        if "72 bytes" in error_msg or "password" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is too long. Please use a shorter password.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post("/login", response_model=Token)
async def login(data: UserLogin):
    """Login with phone and password."""
    user = await AuthService.authenticate_user(data.phone, data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await user.save()
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "phone": user.phone}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=str(user.id),
        name=user.name,
    )


@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "phone": current_user.phone,
        "email": current_user.email,
        "city": current_user.city,
        "platforms_used": current_user.platforms_used,
        "onboarding_completed": current_user.onboarding_completed,
    }
