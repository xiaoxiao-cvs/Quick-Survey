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


class Settings(BaseSettings):
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    upload: UploadSettings = Field(default_factory=UploadSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)


def load_config() -> Settings:
    """从 config.yml 加载配置"""
    config_path = Path("config.yml")
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        return Settings(
            server=ServerSettings(**config_data.get("server", {})),
            database=DatabaseSettings(**config_data.get("database", {})),
            auth=AuthSettings(**config_data.get("auth", {})),
            upload=UploadSettings(**config_data.get("upload", {})),
            cors=CorsSettings(**config_data.get("cors", {})),
        )
    
    return Settings()


@lru_cache
def get_settings() -> Settings:
    return load_config()
