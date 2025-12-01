import hashlib
import base64
import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.core.config import get_settings


class TokenPayload(BaseModel):
    """JWT Token 载荷"""
    sub: str  # username
    adminId: int
    iat: int
    exp: int
    jti: str


class JwtUtil:
    """
    JWT 工具类 - 与 Java 端 JwtUtil 保持一致
    用于验证 Java 端颁发的 JWT Token
    """
    
    @staticmethod
    def _base64url_encode(data: str) -> str:
        """Base64 URL 编码（无 padding）"""
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")
    
    @staticmethod
    def _base64url_decode(data: str) -> str:
        """Base64 URL 解码"""
        # 补齐 padding
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode()
    
    @classmethod
    def _create_signature(cls, data: str) -> str:
        """
        创建签名 - 与 Java 端保持一致
        Java: base64UrlEncode(Base64.getEncoder().encodeToString(SHA256(data + secretKey)))
        """
        settings = get_settings()
        sign_data = data + settings.auth.jwt_secret
        
        # SHA256 哈希
        hash_bytes = hashlib.sha256(sign_data.encode()).digest()
        
        # Base64 编码
        b64_hash = base64.b64encode(hash_bytes).decode()
        
        # Base64 URL 编码
        return base64.urlsafe_b64encode(b64_hash.encode()).decode().rstrip("=")
    
    @classmethod
    def verify_and_decode(cls, token: str) -> Optional[TokenPayload]:
        """
        验证并解析 JWT Token
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            解析后的 payload，验证失败返回 None
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            
            encoded_header, encoded_payload, signature = parts
            
            # 验证签名
            data = f"{encoded_header}.{encoded_payload}"
            expected_signature = cls._create_signature(data)
            
            if signature != expected_signature:
                return None
            
            # 解析 payload
            payload_json = cls._base64url_decode(encoded_payload)
            payload_dict = json.loads(payload_json)
            
            # 检查过期时间
            if datetime.now().timestamp() > payload_dict["exp"]:
                return None
            
            return TokenPayload(**payload_dict)
            
        except Exception:
            return None
    
    @classmethod
    def get_admin_id(cls, token: str) -> Optional[int]:
        """从 Token 中提取管理员 ID"""
        payload = cls.verify_and_decode(token)
        return payload.adminId if payload else None
    
    @classmethod
    def get_username(cls, token: str) -> Optional[str]:
        """从 Token 中提取用户名"""
        payload = cls.verify_and_decode(token)
        return payload.sub if payload else None
    
    @classmethod
    def is_token_expired(cls, token: str) -> bool:
        """检查 Token 是否过期"""
        payload = cls.verify_and_decode(token)
        return payload is None
