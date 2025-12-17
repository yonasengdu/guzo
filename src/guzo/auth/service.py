"""Auth domain service - business logic for authentication."""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from src.guzo.config import settings
from src.guzo.auth.core import User, UserRole, UserCreate, TokenData
from src.guzo.auth.repository import user_repository


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            if user_id is None:
                return None
            return TokenData(user_id=user_id, email=email, role=role)
        except JWTError:
            return None
    
    @classmethod
    async def create_user(cls, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        if await user_repository.email_or_phone_exists(user_data.email, user_data.phone):
            raise ValueError("User with this email or phone already exists")
        
        # Create user
        user = User(
            email=user_data.email,
            phone=user_data.phone,
            full_name=user_data.full_name,
            role=user_data.role,
            password_hash=cls.hash_password(user_data.password),
            language=user_data.language,
        )
        await user_repository.create(user)
        return user
    
    @classmethod
    async def authenticate_user(cls, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = await user_repository.get_by_email(email)
        if not user:
            return None
        if not cls.verify_password(password, user.password_hash):
            return None
        
        # Update last login
        await user_repository.update_last_login(str(user.id))
        return user
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return await user_repository.get_by_id(user_id)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """Get a user by email."""
        return await user_repository.get_by_email(email)

