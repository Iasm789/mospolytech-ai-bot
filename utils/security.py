"""
Модуль безопасности и защиты приложения
ВключаетRate limiting, защита от injection атак, и управление доступом
"""

import time
import asyncio
from typing import Dict, Optional, Callable, Any
from collections import defaultdict
from functools import wraps
from datetime import datetime, timedelta

from aiogram import types
from utils.logger import logger


class RateLimiter:
    """
    Ограничитель частоты запросов (Rate Limiter)
    Предотвращает злоупотребление API и DDOS атаки
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Args:
            max_requests: Максимальное количество запросов
            time_window: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, list] = defaultdict(list)
        self._cleanup_interval = 300  # Очистка каждые 5 минут
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Проверить разрешен ли запрос для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если запрос разрешен
        """
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Удаляем старые запросы
        user_requests[:] = [req_time for req_time in user_requests
                           if now - req_time < self.time_window]
        
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        
        return False
    
    def get_reset_time(self, user_id: int) -> int:
        """
        Получить время до сброса лимита для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Секунды до сброса
        """
        user_requests = self.requests.get(user_id, [])
        if not user_requests:
            return 0
        
        oldest_request = min(user_requests)
        reset_time = int(oldest_request + self.time_window - time.time())
        return max(0, reset_time)
    
    async def cleanup(self) -> None:
        """Периодическая очистка старых данных"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                now = time.time()
                
                for user_id in list(self.requests.keys()):
                    user_requests = self.requests[user_id]
                    user_requests[:] = [req_time for req_time in user_requests
                                       if now - req_time < self.time_window]
                    
                    if not user_requests:
                        del self.requests[user_id]
                
                logger.debug(f"Очищены данные rate limiter'а: осталось {len(self.requests)} пользователей")
            except Exception as e:
                logger.error(f"Ошибка в cleanup rate limiter: {e}")


# Глобальный rate limiter
rate_limiter = RateLimiter(max_requests=30, time_window=60)


def with_rate_limit(
    max_requests: int = 30,
    time_window: int = 60,
    error_message: str = "⏱️ Слишком много запросов. Подождите немного."
) -> Callable:
    """
    Декоратор для ограничения частоты запросов пользователя
    
    Args:
        max_requests: Максимальное количество запросов
        time_window: Временное окно в секундах
        error_message: Сообщение об ошибке
    
    Returns:
        Декоратор функции
    """
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs) -> Any:
            user_id = message.from_user.id
            
            if not limiter.is_allowed(user_id):
                reset_time = limiter.get_reset_time(user_id)
                error_msg = f"{error_message}\nПопробуй через {reset_time} сек."
                await message.answer(error_msg)
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return
            
            return await func(message, *args, **kwargs)
        
        return wrapper
    return decorator


class AccessControl:
    """
    Управление доступом к функциям (RBAC)
    """
    
    def __init__(self, admin_ids: list[int]):
        """
        Args:
            admin_ids: Список ID администраторов
        """
        self.admin_ids = set(admin_ids)
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    def require_admin(self, func: Callable) -> Callable:
        """Декоратор для требования прав администратора"""
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs) -> Any:
            if not self.is_admin(message.from_user.id):
                await message.answer("❌ У вас нет прав доступа к этой функции.")
                logger.warning(f"Unauthorized access attempt by user {message.from_user.id}")
                return
            
            return await func(message, *args, **kwargs)
        
        return wrapper


class SecurityValidator:
    """
    Валидатор безопасности для проверки входных данных
    """
    
    # Черный список опасных паттернов
    DANGEROUS_PATTERNS = [
        r"(\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bunion\b)",  # SQL
        r"(javascript:|onclick|onerror|onload)",  # XSS
        r"(\$\{|\[\{|%7|\\u00)",  # Template injection
    ]
    
    # Максимальная длина сообщения
    MAX_MESSAGE_LENGTH = 4096
    
    @classmethod
    def validate_message_safety(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        Проверить безопасность сообщения
        
        Args:
            text: Текст для проверки
            
        Returns:
            (safe, error_message)
        """
        if not text:
            return False, "Сообщение не может быть пустым"
        
        if len(text) > cls.MAX_MESSAGE_LENGTH:
            return False, f"Сообщение слишком длинное (макс {cls.MAX_MESSAGE_LENGTH} символов)"
        
        import re
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Обнаружена опасная схема в сообщении: {pattern}")
                return False, "❌ Сообщение содержит недопустимые символы или команды"
        
        return True, None
    
    @classmethod
    def sanitize_message(cls, text: str) -> str:
        """
        Очистить сообщение от опасных элементов
        
        Args:
            text: Текст для очистки
            
        Returns:
            Очищенный текст
        """
        import re
        
        # Удаляем потенциально опасные символы
        text = re.sub(r'[`*_\[\](){}~#]', '', text)
        
        # Ограничиваем длину
        if len(text) > cls.MAX_MESSAGE_LENGTH:
            text = text[:cls.MAX_MESSAGE_LENGTH - 3] + "..."
        
        return text.strip()


class SessionManager:
    """
    Менеджер сессий пользователей
    Отслеживает активные сессии и время последней активности
    """
    
    def __init__(self, session_timeout: int = 3600):
        """
        Args:
            session_timeout: Timeout сессии в секундах
        """
        self.session_timeout = session_timeout
        self.sessions: Dict[int, datetime] = {}
    
    def create_session(self, user_id: int) -> None:
        """Создать или обновить сессию пользователя"""
        self.sessions[user_id] = datetime.now()
    
    def is_session_active(self, user_id: int) -> bool:
        """Проверить активна ли сессия"""
        if user_id not in self.sessions:
            return False
        
        last_activity = self.sessions[user_id]
        if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
            del self.sessions[user_id]
            return False
        
        return True
    
    def close_session(self, user_id: int) -> None:
        """Закрыть сессию пользователя"""
        if user_id in self.sessions:
            del self.sessions[user_id]
    
    async def cleanup_expired_sessions(self) -> None:
        """Периодическая очистка истекших сессий"""
        while True:
            try:
                await asyncio.sleep(600)  # Проверяем каждые 10 минут
                now = datetime.now()
                expired_users = [
                    user_id for user_id, last_activity in self.sessions.items()
                    if now - last_activity > timedelta(seconds=self.session_timeout)
                ]
                
                for user_id in expired_users:
                    del self.sessions[user_id]
                
                if expired_users:
                    logger.debug(f"Очищены сессии {len(expired_users)} пользователей")
            except Exception as e:
                logger.error(f"Ошибка при очистке сессий: {e}")


# Глобальный менеджер сессий
session_manager = SessionManager(session_timeout=3600)
