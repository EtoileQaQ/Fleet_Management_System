from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import decode_token
from app.core.rbac import check_role_permission


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current active user."""
    return current_user


def require_read_permission(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require read permission (all authenticated users)."""
    check_role_permission(current_user, "read")
    return current_user


def require_write_permission(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require write permission (ADMIN and RH only)."""
    check_role_permission(current_user, "write")
    return current_user


def require_admin_permission(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require admin permission (ADMIN only)."""
    check_role_permission(current_user, "admin")
    return current_user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
ReadUser = Annotated[User, Depends(require_read_permission)]
WriteUser = Annotated[User, Depends(require_write_permission)]
AdminUser = Annotated[User, Depends(require_admin_permission)]
DbSession = Annotated[AsyncSession, Depends(get_db)]



