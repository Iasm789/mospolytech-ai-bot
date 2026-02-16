import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv()

class Settings(BaseSettings):
    """Основная конфигурация приложения"""
    
    # Bot
    BOT_TOKEN: str = Field(..., env='BOT_TOKEN')
    DEBUG: bool = Field(default=False, env='DEBUG')
    
    # Logging
    LOG_LEVEL: str = Field(default='INFO', env='LOG_LEVEL')
    
    # Admin IDs
    ADMIN_IDS: str = Field(default='', env='ADMIN_IDS')
    
    @property
    def admin_ids_list(self):
        """Парсинг списка admin IDs"""
        if not self.ADMIN_IDS:
            return []
        return [int(id.strip()) for id in self.ADMIN_IDS.split(',') if id.strip()]
    
    class Config:
        env_file = '.env'
        case_sensitive = True
        extra = 'ignore'  # Игнорировать лишние переменные в .env


settings = Settings()
