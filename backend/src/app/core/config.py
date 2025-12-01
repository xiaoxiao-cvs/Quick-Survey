from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import yaml
from pathlib import Path


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


class DatabaseSettings(BaseSettings):
    url: str = "sqlite+aiosqlite:///./data/survey.db"


class AuthSettings(BaseSettings):
    admin_password: str = ""
    
    @property
    def jwt_secret(self) -> str:
        """与 Java 端保持一致的 JWT 密钥"""
        return f"ConvenientAccess-{self.admin_password}"


class UploadSettings(BaseSettings):
    path: str = "./uploads"
    allowed_types: list[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    max_size_mb: int = 10
    
    @property
    def max_size_bytes(self) -> int:
        return self.max_size_mb * 1024 * 1024


class CorsSettings(BaseSettings):
    allowed_origins: list[str] = ["*"]


class TurnstileSettings(BaseSettings):
    """Cloudflare Turnstile 配置"""
    enabled: bool = False
    secret_key: str = ""


class RateLimitSettings(BaseSettings):
    """IP 提交限制配置"""
    enabled: bool = True
    max_submissions_per_day: int = 2


class TimeCheckSettings(BaseSettings):
    """提交时间检测配置"""
    enabled: bool = True
    min_submit_time: int = 10  # 最小提交时间（秒）


class SecuritySettings(BaseSettings):
    """安全配置"""
    turnstile: TurnstileSettings = Field(default_factory=TurnstileSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    time_check: TimeCheckSettings = Field(default_factory=TimeCheckSettings)


class Settings(BaseSettings):
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    upload: UploadSettings = Field(default_factory=UploadSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)


def load_config() -> Settings:
    """从 config.yml 加载配置"""
    config_path = Path("config.yml")
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        # 解析 security 配置
        security_data = config_data.get("security", {})
        security_settings = SecuritySettings(
            turnstile=TurnstileSettings(**security_data.get("turnstile", {})),
            rate_limit=RateLimitSettings(**security_data.get("rate_limit", {})),
            time_check=TimeCheckSettings(**security_data.get("time_check", {})),
        )
        
        return Settings(
            server=ServerSettings(**config_data.get("server", {})),
            database=DatabaseSettings(**config_data.get("database", {})),
            auth=AuthSettings(**config_data.get("auth", {})),
            upload=UploadSettings(**config_data.get("upload", {})),
            cors=CorsSettings(**config_data.get("cors", {})),
            security=security_settings,
        )
    
    return Settings()


@lru_cache
def get_settings() -> Settings:
    return load_config()
