"""
Асинхронные утилиты и оптимизации
Включает кэширование, батчинг запросов, и асинхронные вспомогательные функции
"""

import asyncio
import time
from typing import TypeVar, Callable, Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict

from utils.logger import logger


T = TypeVar('T')
V = TypeVar('V')


class AsyncCache:
    """
    Простой асинхронный кэш с TTL (time to live)
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Args:
            ttl_seconds: Время жизни кэша в секундах
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # Проверяем не истек ли TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Установить значение в кэш"""
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Очистить кэш"""
        self.cache.clear()
    
    def cleanup(self) -> None:
        """Удалить истекшие записи"""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Удалено {len(expired_keys)} истекших записей из кэша")
    
    async def cleanup_periodic(self) -> None:
        """Периодическая очистка кэша"""
        while True:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                self.cleanup()
            except Exception as e:
                logger.error(f"Ошибка при очистке кэша: {e}")


def async_cache(ttl_seconds: int = 3600) -> Callable:
    """
    Декоратор для кэширования результатов асинхронной функции
    
    Args:
        ttl_seconds: Время жизни кэша в секундах
        
    Returns:
        Декоратор функции
    """
    cache = AsyncCache(ttl_seconds=ttl_seconds)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Создаем ключ кэша из аргументов
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Пробуем получить из кэша
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Hit cache for {func.__name__}")
                return cached_value
            
            # Вычисляем результат
            result = await func(*args, **kwargs)
            
            # Сохраняем в кэш
            cache.set(cache_key, result)
            return result
        
        wrapper.__cache = cache
        return wrapper
    
    return decorator


class AsyncBatcher:
    """
    Батчер для группировки и обработки асинхронных операций
    Полезен для оптимизации множественных запросов
    """
    
    def __init__(self, batch_size: int = 10, max_wait: float = 1.0):
        """
        Args:
            batch_size: Размер батча
            max_wait: Максимальное время ожидания перед отправкой батча (в секундах)
        """
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.queue: List[tuple[Any, asyncio.Future]] = []
        self.last_send_time = time.time()
        self._processing = False
    
    async def add(self, item: Any) -> Any:
        """
        Добавить элемент в батч
        
        Args:
            item: Элемент для добавления
            
        Returns:
            Результат обработки элемента
        """
        future: asyncio.Future = asyncio.Future()
        self.queue.append((item, future))
        
        # Проверяем нужно ли отправить батч
        if len(self.queue) >= self.batch_size:
            await self._send_batch()
        elif not self._processing:
            # Запускаем таймер отправки
            asyncio.create_task(self._check_timeout())
        
        return await future
    
    async def _check_timeout(self) -> None:
        """Проверить не превышено ли времяожидания"""
        while len(self.queue) > 0:
            if time.time() - self.last_send_time >= self.max_wait:
                await self._send_batch()
                break
            
            await asyncio.sleep(0.1)
    
    async def _send_batch(self) -> None:
        """Отправить батч"""
        if not self.queue or self._processing:
            return
        
        self._processing = True
        batch = self.queue[:self.batch_size]
        self.queue = self.queue[self.batch_size:]
        
        try:
            # Здесь должна быть реальная обработка батча
            for item, future in batch:
                if not future.done():
                    future.set_result(item)
        except Exception as e:
            logger.error(f"Ошибка при обработке батча: {e}")
            for _, future in batch:
                if not future.done():
                    future.set_exception(e)
        finally:
            self._processing = False
            self.last_send_time = time.time()


class AsyncPool:
    """
    Пул асинхронных рабочих для обработки задач
    """
    
    def __init__(self, worker_count: int = 5):
        """
        Args:
            worker_count: Количество рабочих потоков
        """
        self.worker_count = worker_count
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
    
    async def start(self) -> None:
        """Запустить пул рабочих"""
        if self.running:
            return
        
        self.running = True
        for _ in range(self.worker_count):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
        
        logger.info(f"✅ AsyncPool запущен с {self.worker_count} рабочими")
    
    async def stop(self) -> None:
        """Остановить пул рабочих"""
        self.running = False
        
        # Ждем завершения всех рабочих
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("✅ AsyncPool остановлен")
    
    async def submit(self, coro: Any) -> Any:
        """
        Добавить корутину в очередь
        
        Args:
            coro: Корутина для выполнения
            
        Returns:
            Результат выполнения корутины
        """
        future: asyncio.Future = asyncio.Future()
        await self.queue.put((coro, future))
        return await future
    
    async def _worker(self) -> None:
        """Рабочий процесс"""
        while self.running:
            try:
                # Получаем задачу из очереди с таймаутом
                try:
                    coro, future = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Выполняем задачу
                try:
                    result = await coro
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Ошибка в AsyncPool worker: {e}")


async def gather_with_limit(
    coros: List[Any],
    limit: int = 5,
    return_exceptions: bool = False
) -> List[Any]:
    """
    Выполнить множество корутин с ограничением одновременного выполнения
    
    Args:
        coros: Список корутин для выполнения
        limit: Максимальное количество одновременных корутин
        return_exceptions: Возвращать ли исключения в результатах
        
    Returns:
        Список результатов
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def sem_coro(coro: Any) -> Any:
        async with semaphore:
            return await coro
    
    return await asyncio.gather(
        *[sem_coro(coro) for coro in coros],
        return_exceptions=return_exceptions
    )


async def retry_async(
    coro_func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    exponential: bool = True
) -> Any:
    """
    Повторить асинхронную функцию при ошибке
    
    Args:
        coro_func: Асинхронная функция
        max_attempts: Максимальное количество попыток
        delay: Задержка между попытками
        exponential: Использовать экспоненциальный backoff
        
    Returns:
        Результат функции
    """
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return await coro_func()
        except Exception as e:
            if attempt >= max_attempts - 1:
                raise
            
            logger.warning(f"Попытка {attempt + 1} провалилась, повтор через {current_delay}с...")
            await asyncio.sleep(current_delay)
            
            if exponential:
                current_delay *= 2


class PerformanceMonitor:
    """
    Монитор производительности асинхронных операций
    """
    
    def __init__(self):
        self.operations: Dict[str, list] = defaultdict(list)
    
    async def measure(self, name: str, coro: Any) -> Any:
        """
        Измерить время выполнения корутины
        
        Args:
            name: Имя операции
            coro: Корутина для выполнения
            
        Returns:
            Результат корутины
        """
        start_time = time.time()
        
        try:
            result = await coro
            duration = time.time() - start_time
            self.operations[name].append({
                'duration': duration,
                'error': None,
                'timestamp': datetime.now()
            })
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.operations[name].append({
                'duration': duration,
                'error': str(e),
                'timestamp': datetime.now()
            })
            raise
    
    def get_stats(self, name: str) -> Dict[str, any]:
        """Получить статистику по операции"""
        if name not in self.operations:
            return {}
        
        ops = self.operations[name]
        durations = [op['duration'] for op in ops]
        errors = [op for op in ops if op['error']]
        
        return {
            'count': len(ops),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'error_count': len(errors),
            'error_rate': len(errors) / len(ops) if ops else 0
        }
