from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.jwt import JwtUtil, TokenPayload


security = HTTPBearer(auto_error=False)


class CurrentUser:
    """当前用户信息"""
    def __init__(self, payload: TokenPayload):
        self.id = payload.adminId
        self.username = payload.sub


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> CurrentUser:
    """
    获取当前登录用户（必须登录）
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = JwtUtil.verify_and_decode(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return CurrentUser(payload)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    获取当前用户（可选，未登录返回 None）
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = JwtUtil.verify_and_decode(token)
    
    if payload is None:
        return None
    
    return CurrentUser(payload)
