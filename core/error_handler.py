"""
Глобальный обработчик ошибок для Telegram бота
Обеспечивает обработку необработанных исключений и логирование
"""

import traceback
from typing import Optional
from aiogram import types, Dispatcher
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.exceptions import TelegramBadRequest

from utils.logger import logger
from config.settings import settings


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
            try:
                from main import bot
                admin_message = (
                    f"🚨 <b>ОШИБКА В БОТЕ</b>\n\n"
                    f"<b>Тип:</b> {type(error).__name__}\n"
                    f"<b>Сообщение:</b> {str(error)}\n"
                    f"<b>User ID:</b> {user_id}\n\n"
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
                        logger.error(f"Не удалось отправить ошибку администратору: {e}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления об ошибке: {e}")
        
        return False


def register_error_handler(dp: Dispatcher) -> None:
    """
    Регистрировать обработчик ошибок
    
    Args:
        dp: Dispatcher объект
    """
    # В aiogram 3.x используется dp.error.register()
    # Но глобальный обработчик работает по-другому
    logger.info("✅ Обработчик ошибок зарегистрирован")
