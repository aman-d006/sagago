from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    DATABASE_URL: str
    ALLOWED_ORIGINS: str = ""  
    SECRET_KEY: str
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_USE_FALLBACK: bool = True
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    
    USE_TURSO: Optional[bool] = False
    TURSO_DATABASE_URL: Optional[str] = None
    TURSO_AUTH_TOKEN: Optional[str] = None

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        """Get the list of allowed origins"""
     
        base_origins = [
            "https://sagago.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "https://sagago-7.onrender.com"
        ]
        
        if self.ALLOWED_ORIGINS:
            env_origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
            base_origins.extend(env_origins)
        
      
        return list(set(base_origins))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

ALLOWED_ORIGINS_LIST = settings.allowed_origins_list

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "stories"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "avatars"), exist_ok=True)