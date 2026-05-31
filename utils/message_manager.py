"""
Утилиты для управления сообщениями в Telegram
Обеспечивает удобный интерфейс для отправки и редактирования сообщений

УЛУЧШЕНИЯ:
- Исправлена утечка памяти в _user_last_message_ids
- Добавлен TTL для записей в кэше
- Улучшена логика обработки ошибок
- Добавлена очистка кэша для неактивных пользователей
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from config.constants import MAX_USERS_IN_MESSAGE_CACHE, MESSAGE_CACHE_TTL
from utils.logger import logger


class MessageCache:
    """Кэш сообщений с поддержкой TTL и автоочистки"""

    def __init__(
        self, max_users: int = MAX_USERS_IN_MESSAGE_CACHE, ttl_seconds: int = MESSAGE_CACHE_TTL
    ):
        self.max_users = max_users
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[int, tuple] = {}  # {user_id: (message_id, timestamp)}
        self._cleanup_running = False

    def get(self, user_id: int) -> Optional[int]:
        """
        Получить ID последнего сообщения пользователя

        Args:
            user_id: ID пользователя в Telegram

        Returns:
            ID сообщения или None если кэш истек или не существует
        """
        if user_id not in self._cache:
            return None

        message_id, timestamp = self._cache[user_id]

        # Проверяем TTL
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self._cache[user_id]
            return None

        return message_id

    def set(self, user_id: int, message_id: int) -> None:
        """
        Установить ID последнего сообщения пользователя

        Args:
            user_id: ID пользователя в Telegram
            message_id: ID сообщения
        """
        # Если кэш переполнен, очищаем старые записи
        if len(self._cache) >= self.max_users:
            self._cleanup_old_entries()

        self._cache[user_id] = (message_id, datetime.now())

    def delete(self, user_id: int) -> None:
        """Удалить запись из кэша"""
        if user_id in self._cache:
            del self._cache[user_id]

    def _cleanup_old_entries(self) -> None:
        """Удалить старые записи из кэша"""
        current_time = datetime.now()
        expired_users = [
            user_id
            for user_id, (_, timestamp) in self._cache.items()
            if current_time - timestamp > timedelta(seconds=self.ttl_seconds)
        ]

        for user_id in expired_users:
            del self._cache[user_id]

        # Если кэш еще переполнен, удаляем самые старые записи
        if len(self._cache) >= self.max_users:
            sorted_users = sorted(
                self._cache.items(), key=lambda x: x[1][1]  # Сортируем по timestamp
            )
            # Удаляем 20% самых старых
            to_delete = len(sorted_users) // 5
            for user_id, _ in sorted_users[:to_delete]:
                del self._cache[user_id]

    def get_stats(self) -> dict:
        """Получить статистику кэша"""
        return {
            "total_users": len(self._cache),
            "max_users": self.max_users,
            "ttl_seconds": self.ttl_seconds,
        }


# Глобальный кэш сообщений
_message_cache = MessageCache()


def get_last_message_id(user_id: int) -> Optional[int]:
    """Получить ID последнего сообщения пользователя"""
    return _message_cache.get(user_id)


def set_last_message_id(user_id: int, message_id: int) -> None:
    """Установить ID последнего сообщения пользователя"""
    _message_cache.set(user_id, message_id)


def reset_last_message_id(user_id: int) -> None:
    """Удалить ID последнего сообщения пользователя"""
    _message_cache.delete(user_id)


def get_message_cache_stats() -> dict:
    """Получить статистику кэша сообщений"""
    return _message_cache.get_stats()


async def send_or_edit_message(
    message: types.Message,
    text: str,
    reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, None] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> Optional[types.Message]:
    """
    Отправить новое сообщение или отредактировать последнее

    Логика:
    - Если последнее сообщение содержит InlineKeyboardMarkup, редактируем его
    - Если нужна ReplyKeyboardMarkup, всегда отправляем новое сообщение
    - Если редактирование не удалось, отправляем новое

    Args:
        message: Объект сообщения из обработчика
        text: Текст сообщения
        reply_markup: Клавиатура (обычная или inline)
        parse_mode: Режим парсинга (HTML, Markdown)
        disable_web_page_preview: Отключить просмотр веб-страницы для ссылок

    Returns:
        Отправленное или отредактированное сообщение или None при ошибке
    """
    user_id = message.from_user.id
    last_message_id = get_last_message_id(user_id)

    try:
        # Пытаемся редактировать, только если:
        # 1. У нас есть последнее сообщение
        # 2. Нужна inline клавиатура (обычная не поддерживается для редактирования)
        if last_message_id and isinstance(reply_markup, (InlineKeyboardMarkup, type(None))):
            try:
                edited_message = await message.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=last_message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                )
                logger.debug(
                    f"✏️ Сообщение отредактировано (user_id: {user_id}, msg_id: {last_message_id})"
                )
                return edited_message

            except TelegramBadRequest as e:
                # Сообщение уже удалено или другая критическая ошибка
                logger.debug(f"⚠️ Не удалось отредактировать сообщение: {e}")
                reset_last_message_id(user_id)

        if isinstance(reply_markup, ReplyKeyboardMarkup):
            # Для обычной клавиатуры всегда отправляем новое сообщение
            reset_last_message_id(user_id)

        # Отправляем новое сообщение
        sent_message = await message.answer(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )

        # Сохраняем ID нового сообщения
        set_last_message_id(user_id, sent_message.message_id)
        logger.debug(
            f"📤 Новое сообщение отправлено (user_id: {user_id}, msg_id: {sent_message.message_id})"
        )
        return sent_message

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке/редактировании сообщения: {e}", exc_info=True)
        # Как последняя попытка, отправляем новое сообщение без сохранения состояния
        try:
            sent_message = await message.answer(text=text, parse_mode=parse_mode)
            set_last_message_id(user_id, sent_message.message_id)
            return sent_message
        except Exception as e2:
            logger.error(f"❌ Не удалось отправить даже простое сообщение: {e2}")
            return None


async def delete_message(user_id: int, bot: Bot, target_message_id: Optional[int] = None) -> bool:
    """
    Удалить сообщение пользователя

    Args:
        user_id: ID пользователя
        bot: Объект бота
        target_message_id: ID конкретного сообщения для удаления
                          Если None, удаляет последнее известное сообщение

    Returns:
        True если удалось, False иначе
    """
    try:
        message_id = target_message_id or get_last_message_id(user_id)

        if not message_id:
            logger.warning(f"⚠️ Нет сообщения для удаления для пользователя {user_id}")
            return False

        await bot.delete_message(chat_id=user_id, message_id=message_id)
        logger.debug(f"🗑️ Сообщение удалено (user_id: {user_id}, msg_id: {message_id})")

        # Только если удалили последнее сообщение, очищаем кэш
        if message_id == get_last_message_id(user_id):
            reset_last_message_id(user_id)

        return True

    except TelegramBadRequest as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении сообщения: {e}")
        return False


def clear_user_cache(user_id: int) -> None:
    """Полностью очистить кэш для пользователя"""
    reset_last_message_id(user_id)
    logger.debug(f"✨ Кэш сообщений очищен для пользователя {user_id}")
