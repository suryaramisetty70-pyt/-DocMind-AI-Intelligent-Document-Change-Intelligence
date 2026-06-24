"""Authentication utilities - Handles JWT tokens and Password hashing."""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from passlib.context import CryptContext

# ═══════════════════════════════════════════════════════════
# PASSWORD HASHING CONFIG
# ═══════════════════════════════════════════════════════════
# Uses bcrypt algorithm for secure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ═══════════════════════════════════════════════════════════
# JWT CONFIGURATION
# ═══════════════════════════════════════════════════════════
SECRET_KEY = os.getenv("SECRET_KEY", "docfinder-secret-key-change-in-production-2024")
ALGORITHM = "HS256"  # JWT signing algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# ═══════════════════════════════════════════════════════════
# PASSWORD FUNCTIONS
# ═══════════════════════════════════════════════════════════

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: The password user entered (e.g., "secret123")
        hashed_password: The hashed password from database (e.g., "$2b$12$...")
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)

# ═══════════════════════════════════════════════════════════
# JWT TOKEN FUNCTIONS
# ═══════════════════════════════════════════════════════════

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT (JSON Web Token) for authentication.
    
    Args:
        data: Dictionary containing user data to encode
              Example: {"sub": "1"} where "1" is user_id
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
        Example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration time to token
    to_encode.update({"exp": expire})
    
    # Encode and return token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload as dictionary
        Example: {"sub": "1", "exp": 1234567890}
    
    Raises:
        jwt.PyJWTError: If token is invalid or expired
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_current_user_id(token: str) -> Optional[int]:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        User ID as integer if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except Exception:
        return None