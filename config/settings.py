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
    
    # GigaChat API
    GIGACHAT_CLIENT_ID: str = Field(default='', env='GIGACHAT_CLIENT_ID')
    GIGACHAT_CLIENT_SECRET: str = Field(default='', env='GIGACHAT_CLIENT_SECRET')
    GIGACHAT_SCOPE: str = Field(default='GIGACHAT_API_PERS', env='GIGACHAT_SCOPE')
    GIGACHAT_AUTH_URL: str = Field(
        default='https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
        env='GIGACHAT_AUTH_URL'
    )
    GIGACHAT_API_URL: str = Field(
        default='https://gigachat.devices.sberbank.ru/api/v1',
        env='GIGACHAT_API_URL'
    )
    GIGACHAT_MODEL: str = Field(default='GigaChat', env='GIGACHAT_MODEL')
    
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


settings = Settings()
