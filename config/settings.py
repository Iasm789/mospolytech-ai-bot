"""
Конфигурация приложения
Загружается из переменных окружения с валидацией
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, validator, ValidationError

load_dotenv()


class Settings(BaseSettings):
    """Основная конфигурация приложения с валидацией"""
    
    # Bot configuration
    BOT_TOKEN: str = Field(..., env='BOT_TOKEN', min_length=10)
    DEBUG: bool = Field(default=False, env='DEBUG')
    
    # Logging configuration
    LOG_LEVEL: str = Field(default='INFO', env='LOG_LEVEL')
    LOG_FILE: str = Field(default='bot.log', env='LOG_FILE')
    MAX_LOG_SIZE: int = Field(default=10485760, env='MAX_LOG_SIZE')  # 10 MB
    
    # Admin IDs (comma-separated)
    ADMIN_IDS: str = Field(default='', env='ADMIN_IDS')
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = Field(default=30, env='RATE_LIMIT_REQUESTS')
    RATE_LIMIT_WINDOW: int = Field(default=60, env='RATE_LIMIT_WINDOW')
    
    # Sessions
    SESSION_TIMEOUT: int = Field(default=3600, env='SESSION_TIMEOUT')  # 1 hour
    
    # Timeouts
    REQUEST_TIMEOUT: int = Field(default=30, env='REQUEST_TIMEOUT')
    PARSER_TIMEOUT: int = Field(default=60, env='PARSER_TIMEOUT')
    
    # Cache configuration
    CACHE_ENABLED: bool = Field(default=True, env='CACHE_ENABLED')
    CACHE_DIR: str = Field(default='data/cache', env='CACHE_DIR')
    CACHE_EXPIRY: int = Field(default=86400, env='CACHE_EXPIRY')  # 24 hours
    
    # Feature flags
    USE_SELENIUM: bool = Field(default=True, env='USE_SELENIUM')
    ENABLE_NOTIFICATIONS: bool = Field(default=True, env='ENABLE_NOTIFICATIONS')
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Валидировать уровень логирования"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            raise ValueError(f'LOG_LEVEL должен быть одним из: {valid_levels}')
        return v
    
    @validator('RATE_LIMIT_REQUESTS', 'RATE_LIMIT_WINDOW', 'SESSION_TIMEOUT',
               'REQUEST_TIMEOUT', 'PARSER_TIMEOUT', 'CACHE_EXPIRY', 'MAX_LOG_SIZE')
    def validate_positive_integers(cls, v):
        """Валидировать положительные целые числа"""
        if v <= 0:
            raise ValueError('Значение должно быть положительным числом')
        return v
    
    @validator('BOT_TOKEN')
    def validate_bot_token(cls, v):
        """Валидировать токен бота"""
        if not v or len(v) < 20:
            raise ValueError('Неверный формат BOT_TOKEN')
        return v
    
    @property
    def admin_ids_list(self) -> list[int]:
        """Парсинг списка admin IDs с валидацией"""
        if not self.ADMIN_IDS:
            return []
        
        try:
            admin_ids = []
            for id_str in self.ADMIN_IDS.split(','):
                id_str = id_str.strip()
                if id_str and id_str.isdigit():
                    admin_ids.append(int(id_str))
            return admin_ids
        except (ValueError, AttributeError) as e:
            raise ValueError(f'Ошибка при парсинге ADMIN_IDS: {e}')
    
    class Config:
        env_file = '.env'
        case_sensitive = True
        extra = 'ignore'  # Игнорировать лишние переменные в .env


def validate_settings() -> Optional[str]:
    """
    Валидировать все параметры конфигурации
    
    Returns:
        Сообщение об ошибке или None если всё ОК
    """
    try:
        global settings
        settings = Settings()
        
        # Проверяем критические параметры
        if not settings.BOT_TOKEN:
            return "❌ Ошибка: BOT_TOKEN не установлен"
        
        # Логируем успешную инициализацию конфигурации
        from utils.logger import logger
        logger.info("✅ Конфигурация успешно загружена и валидирована")
        
        return None
    except ValidationError as e:
        error_msg = f"❌ Ошибка валидации конфигурации: {e}"
        return error_msg
    except Exception as e:
        error_msg = f"❌ Критическая ошибка конфигурации: {e}"
        return error_msg


# Инициализация конфигурации
try:
    settings = Settings()
except ValidationError as e:
    print(f"❌ Ошибка при загрузке конфигурации: {e}")
    raise

