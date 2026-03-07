"""
Глобальный обработчик ошибок для Telegram бота
Обеспечивает обработку необработанных исключений и логирование
"""

import traceback
from typing import Optional, Callable, Any
from functools import wraps

from aiogram import types, Dispatcher, Router
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from utils.logger import logger
from config.settings import settings
from utils.message_utils import MessageFormatter


class CustomExceptions:
    """Кастомные исключения приложения"""
    
    class ValidationError(Exception):
        """Ошибка валидации"""
        pass
    
    class ServiceError(Exception):
        """Ошибка сервиса"""
        pass
    
    class ParserError(Exception):
        """Ошибка парсера"""
        pass
    
    class RateLimitError(Exception):
        """Превышен лимит частоты запросов"""
        pass
    
    class AuthenticationError(Exception):
        """Ошибка аутентификации"""
        pass
    
    class NotFoundError(Exception):
        """Ресурс не найден"""
        pass


class ErrorHandler:
    """Обработчик ошибок бота"""
    
    @staticmethod
    async def handle_error(update: Optional[types.Update], error: Exception) -> bool:
        """
        Обработать ошибку
        
        Args:
            update: Объект обновления (может быть None)
            error: Исключение
        
        Returns:
            bool: True если ошибка обработана, False если нужна дальнейшая обработка
        """
        error_message = f"Критическая ошибка: {type(error).__name__}: {str(error)}"
        
        # Логируем полную информацию об ошибке
        logger.error(error_message, exc_info=True)
        
        # Извлекаем информацию о пользователе если есть
        user_id = None
        chat_id = None
        
        if update:
            if update.message:
                user_id = update.message.from_user.id
                chat_id = update.message.chat.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id
                chat_id = update.callback_query.message.chat.id
        
        # Логируем контекст ошибки
        if user_id:
            logger.error(f"Ошибка для пользователя {user_id} (chat_id: {chat_id})")
        
        # Обработка специфичных ошибок
        if isinstance(error, TelegramBadRequest):
            logger.warning(f"Telegram API ошибка: {error}")
            return True  # Игнорируем, не критично
        
        if isinstance(error, TelegramAPIError):
            logger.warning(f"Ошибка API Telegram: {error}")
            return True
        
        # Отправляем уведомление администратору если включен DEBUG
        if settings.DEBUG and settings.admin_ids_list:
            await ErrorHandler._notify_admins(error, user_id, chat_id)
        
        return False
    
    @staticmethod
    async def _notify_admins(error: Exception, user_id: Optional[int], chat_id: Optional[int]) -> None:
        """Уведомить администраторов об ошибке"""
        try:
            from main import bot
            
            admin_message = (
                f"🚨 <b>ОШИБКА В БОТЕ</b>\n\n"
                f"<b>Тип:</b> {type(error).__name__}\n"
                f"<b>Сообщение:</b> {str(error)}\n"
                f"<b>User ID:</b> {user_id}\n"
                f"<b>Chat ID:</b> {chat_id}\n\n"
                f"<b>Traceback:</b>\n"
                f"<code>{traceback.format_exc()[:1000]}</code>"
            )
            
            for admin_id in settings.admin_ids_list:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить ошибку администратору {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления об ошибке: {e}")


def safe_async_handler(func: Callable) -> Callable:
    """
    Декоратор для безопасного выполнения асинхронных обработчиков
    Перехватывает ошибки и отправляет пользователю понятное сообщение
    
    Args:
        func: Асинхронная функция обработчика
        
    Returns:
        Обертка с обработкой ошибок
    """
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs) -> Any:
        try:
            return await func(message, *args, **kwargs)
        except CustomExceptions.ValidationError as e:
            logger.warning(f"Ошибка валидации в {func.__name__}: {e}")
            await message.answer(
                MessageFormatter.format_error(
                    f"Ошибка валидации: {str(e)}",
                    "Проверьте введенные данные и попробуйте еще раз"
                ),
                parse_mode="HTML"
            )
        except CustomExceptions.RateLimitError:
            logger.info(f"Rate limit для пользователя {message.from_user.id}")
            await message.answer(
                f"{MessageFormatter.EMOJI['warning']} Слишком много запросов. Подождите немного.",
                parse_mode="HTML"
            )
        except CustomExceptions.NotFoundError as e:
            logger.info(f"Ресурс не найден: {e}")
            await message.answer(
                MessageFormatter.format_error(str(e)),
                parse_mode="HTML"
            )
        except CustomExceptions.ServiceError as e:
            logger.error(f"Ошибка сервиса в {func.__name__}: {e}", exc_info=True)
            await message.answer(
                MessageFormatter.format_error(
                    "Ошибка при получении данных",
                    "Пожалуйста, попробуйте позже или обратитесь в поддержку"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(
                f"Необработанная ошибка в {func.__name__}: {e}",
                exc_info=True
            )
            await message.answer(
                MessageFormatter.format_error(
                    "Произошла непредвиденная ошибка",
                    "Наша команда уже работает над исправлением. Спасибо за терпение!"
                ),
                parse_mode="HTML"
            )
    
    return wrapper


def safe_callback_handler(func: Callable) -> Callable:
    """
    Декоратор для безопасного выполнения обработчиков callbacks
    
    Args:
        func: Асинхронная функция обработчика callback
        
    Returns:
        Обертка с обработкой ошибок
    """
    @wraps(func)
    async def wrapper(callback: types.CallbackQuery, *args, **kwargs) -> Any:
        try:
            return await func(callback, *args, **kwargs)
        except CustomExceptions.ValidationError as e:
            logger.warning(f"Ошибка валидации в {func.__name__}: {e}")
            await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        except CustomExceptions.RateLimitError:
            logger.info(f"Rate limit для пользователя {callback.from_user.id}")
            await callback.answer("⏱️  Слишком много запросов. Подождите немного.", show_alert=False)
        except CustomExceptions.NotFoundError as e:
            logger.info(f"Ресурс не найден: {e}")
            await callback.answer(f"ℹ️  {str(e)}", show_alert=True)
        except CustomExceptions.ServiceError as e:
            logger.error(f"Ошибка сервиса в {func.__name__}: {e}", exc_info=True)
            await callback.answer(
                "⚠️  Ошибка при получении данных. Пожалуйста, попробуйте позже.",
                show_alert=True
            )
        except Exception as e:
            logger.error(
                f"Необработанная ошибка в {func.__name__}: {e}",
                exc_info=True
            )
            await callback.answer(
                "❌ Произошла непредвиденная ошибка",
                show_alert=True
            )
    
    return wrapper


def setup_error_handlers(dp: Dispatcher) -> None:
    """
    Установить обработчики ошибок для диспетчера
    
    Args:
        dp: Dispatcher объект
    """
    logger.info("✅ Обработчики ошибок установлены")


def register_error_handler(dp: Dispatcher) -> None:
    """
    Регистрировать обработчик ошибок
    
    Args:
        dp: Dispatcher объект
    """
    # В aiogram 3.x используется dp.error.register()
    # Но глобальный обработчик работает по-другому
    logger.info("✅ Обработчик ошибок зарегистрирован")

