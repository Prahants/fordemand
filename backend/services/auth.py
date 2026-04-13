"""
auth.py - Simple role-based access control helpers.
"""

from fastapi import Header, HTTPException

VALID_ROLES = {"admin", "manager", "staff"}


def require_role(allowed_roles: set[str]):
    """FastAPI dependency to guard endpoints using `X-Role` header."""

    def _checker(x_role: str = Header(default="staff", alias="X-Role")) -> str:
        role = (x_role or "staff").lower()
        if role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="Invalid role in X-Role header")
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return role

    return _checker
