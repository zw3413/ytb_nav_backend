from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "YouTube Data Tool"
    
    # YouTube API配置
    YOUTUBE_API_KEY: Optional[str] = None
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str]
    OPENAI_API_BASE: str
    OPENAI_TEMPERATURE: float
    OPENAI_MODEL: str
    
    # 数据库配置
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # 调试模式
    DEBUG: bool
    
    class Config:
        env_file = "/app/.env"
        case_sensitive = True

def get_settings() -> Settings:
    return Settings() 