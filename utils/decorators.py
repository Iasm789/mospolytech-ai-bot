"""
Декораторы для обработчиков и сервисов
Обеспечивает переиспользуемые паттерны обработки ошибок и логирования
"""

import asyncio
import functools
from typing import Callable, Any, Optional, Coroutine
from aiogram import types

from utils.logger import logger


def with_error_handling(
    error_message: str = "❌ Произошла ошибка. Попробуй позже.",
    log_error: bool = True
) -> Callable:
    """
    Декоратор для обработки ошибок в обработчиках сообщений
    
    Args:
        error_message: Сообщение об ошибке для пользователя
        log_error: Логировать ли выполняющуюся ошибку
    
    Example:
        @with_error_handling(error_message="❌ Не удалось получить данные")
        async def my_handler(message: types.Message):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs) -> Any:
            try:
                return await func(message, *args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Ошибка в {func.__name__}: {e}", exc_info=True)
                await message.answer(error_message)
        return wrapper
    return decorator


def with_retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    exponential: bool = True
) -> Callable:
    """
    Декоратор для повторного выполнения функции при ошибке
    
    Args:
        max_attempts: Максимальное количество попыток
        delay_seconds: Задержка между попытками (в секундах)
        exponential: Использовать ли экспоненциальную задержку
    
    Example:
        @with_retry(max_attempts=3, delay_seconds=1.0)
        async def get_data_from_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            current_delay = delay_seconds
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Все {max_attempts} попытки исчерпаны для {func.__name__}")
                        raise
                    
                    if exponential:
                        current_delay = delay_seconds * (2 ** (attempt - 1))
                    
                    logger.warning(
                        f"Попытка {attempt}/{max_attempts} провалилась для {func.__name__}. "
                        f"Ожидание {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
        
        return wrapper
    return decorator


def with_timeout(timeout_seconds: float = 30.0) -> Callable:
    """
    Декоратор для установки timeout на асинхронную функцию
    
    Args:
        timeout_seconds: Timeout в секундах
    
    Example:
        @with_timeout(timeout_seconds=10.0)
        async def long_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout {timeout_seconds}s для {func.__name__}")
                raise
        return wrapper
    return decorator


def with_logging(
    log_args: bool = False,
    log_result: bool = True,
    level: str = "info"
) -> Callable:
    """
    Декоратор для логирования вызовов функции
    
    Args:
        log_args: Логировать ли аргументы функции
        log_result: Логировать ли результат
        level: Уровень логирования (info, debug, warning)
    
    Example:
        @with_logging(log_args=True, log_result=True)
        async def process_data(data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            log_func = getattr(logger, level)
            
            if log_args:
                log_func(f"🔵 {func.__name__} started with args={args}, kwargs={kwargs}")
            else:
                log_func(f"🔵 {func.__name__} started")
            
            try:
                result = await func(*args, **kwargs)
                
                if log_result:
                    log_func(f"✅ {func.__name__} completed with result={result}")
                else:
                    log_func(f"✅ {func.__name__} completed")
                
                return result
            except Exception as e:
                logger.error(f"❌ {func.__name__} failed: {e}")
                raise
        
        return wrapper
    return decorator


def validate_message_not_none(func: Callable) -> Callable:
    """
    Декоратор проверяет что message не None
    
    Example:
        @validate_message_not_none
        async def my_handler(message: types.Message):
            ...
    """
    @functools.wraps(func)
    async def wrapper(message: Optional[types.Message], *args, **kwargs) -> Any:
        if message is None:
            logger.warning(f"{func.__name__}: message is None")
            return
        return await func(message, *args, **kwargs)
    
    return wrapper


def ratelimit(calls_per_minute: int = 30) -> Callable:
    """
    Декоратор для ограничения количества вызовов в минуту
    
    Args:
        calls_per_minute: Максимальное количество вызовов в минуту
    
    Example:
        @ratelimit(calls_per_minute=10)
        async def expensive_operation():
            ...
    """
    last_calls = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            user_id = None
            if args and isinstance(args[0], types.Message):
                user_id = args[0].from_user.id
            
            if user_id:
                import time
                current_time = time.time()
                
                if user_id not in last_calls:
                    last_calls[user_id] = []
                
                # Удаляем старые вызовы (старше 1 минуты)
                last_calls[user_id] = [
                    call_time for call_time in last_calls[user_id]
                    if current_time - call_time < 60
                ]
                
                if len(last_calls[user_id]) >= calls_per_minute:
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    raise RuntimeError(
                        f"❌ Слишком много запросов. Максимум {calls_per_minute} в минуту."
                    )
                
                last_calls[user_id].append(current_time)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
