from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status
from app.models.user import UserRole, User


# Define role permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {"read", "write", "delete", "admin"},
    UserRole.RH: {"read", "write"},
    UserRole.VIEWER: {"read"},
}


def has_permission(user: User, required_permission: str) -> bool:
    """Check if user has the required permission."""
    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return required_permission in user_permissions


def check_role_permission(user: User, required_permission: str) -> None:
    """
    Check if user has required permission, raise HTTPException if not.
    
    Permissions:
    - read: Can view data
    - write: Can create and update data
    - delete: Can delete data
    - admin: Full administrative access
    """
    if not has_permission(user, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permission}. Your role: {user.role.value}"
        )


def require_role(*allowed_roles: UserRole):
    """
    Decorator to require specific roles for an endpoint.
    Use this for explicit role-based access control.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Find current_user in kwargs
            current_user = kwargs.get("current_user")
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RoleChecker:
    """
    Dependency class for checking roles.
    Usage: Depends(RoleChecker([UserRole.ADMIN, UserRole.RH]))
    """
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user



