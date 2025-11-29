"""
GigMoney Guru - Authentication Service
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from beanie import PydanticObjectId

from app.config import settings
from app.models.user import User
from app.schemas.auth import TokenData
from app.services.allocation import AllocationService


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bcrypt has a 72-byte limit
MAX_PASSWORD_LENGTH = 72


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def _truncate_password(password: str) -> str:
        """Truncate password to 72 bytes for bcrypt compatibility."""
        # Encode to bytes, truncate, decode back
        return password.encode('utf-8')[:MAX_PASSWORD_LENGTH].decode('utf-8', errors='ignore')
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(AuthService._truncate_password(password))
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(AuthService._truncate_password(plain_password), hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            user_id: str = payload.get("sub")
            phone: str = payload.get("phone")
            
            if user_id is None:
                return None
            
            return TokenData(user_id=user_id, phone=phone)
        except JWTError:
            return None
    
    @staticmethod
    async def authenticate_user(phone: str, password: str) -> Optional[User]:
        """Authenticate a user by phone and password."""
        user = await User.find_one(User.phone == phone)
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    async def register_user(
        name: str,
        phone: str,
        password: str,
        email: Optional[str] = None,
        city: str = "Mumbai"
    ) -> User:
        """Register a new user."""
        # Check if phone already exists
        existing = await User.find_one(User.phone == phone)
        if existing:
            raise ValueError("Phone number already registered")
        
        # Create user
        user = User(
            name=name,
            phone=phone,
            email=email,
            city=city,
            password_hash=AuthService.hash_password(password),
        )
        
        await user.insert()
        
        # Create default buckets for the new user
        await AllocationService.create_default_buckets(str(user.id))
        
        return user
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            return await User.get(PydanticObjectId(user_id))
        except:
            return None
