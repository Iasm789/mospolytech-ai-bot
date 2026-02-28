"""
Утилиты для управления сообщениями в Telegram
Обеспечивает удобный интерфейс для отправки и редактирования сообщений
"""

from typing import Optional, Union
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from utils.logger import logger

# Хранилище ID последних сообщений для каждого пользователя
_user_last_message_ids = {}


def get_last_message_id(user_id: int) -> Optional[int]:
    """Получить ID последнего сообщения пользователя"""
    return _user_last_message_ids.get(user_id)


def set_last_message_id(user_id: int, message_id: int) -> None:
    """Установить ID последнего сообщения пользователя"""
    _user_last_message_ids[user_id] = message_id


def reset_last_message_id(user_id: int) -> None:
    """Удалить ID последнего сообщения пользователя"""
    if user_id in _user_last_message_ids:
        del _user_last_message_ids[user_id]


async def send_or_edit_message(
    message: types.Message,
    text: str,
    reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, None] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True
) -> Optional[types.Message]:
    """
    Отправить новое сообщение или отредактировать последнее
    
    Args:
        message: Объект сообщения из обработчика
        text: Текст сообщения
        reply_markup: Клавиатура (обычная или inline)
        parse_mode: Режим парсинга (HTML, Markdown)
        disable_web_page_preview: Отключить просмотр веб-страницы для ссылок
    
    Returns:
        Отправленное или отредактированное сообщение
    """
    user_id = message.from_user.id
    last_message_id = get_last_message_id(user_id)
    
    try:
        # Если у нас есть ID последнего сообщения, пытаемся его отредактировать
        if last_message_id:
            # При редактировании используем только InlineKeyboardMarkup
            # ReplyKeyboardMarkup не поддерживается для редактирования сообщений
            can_edit = True
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                # Не пытаемся редактировать, если нужна обычная клавиатура
                can_edit = False
                reset_last_message_id(user_id)
            
            if can_edit:
                try:
                    edit_markup = None
                    if isinstance(reply_markup, InlineKeyboardMarkup):
                        edit_markup = reply_markup
                    
                    edited_message = await message.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=last_message_id,
                        text=text,
                        reply_markup=edit_markup,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview
                    )
                    logger.debug(f"✏️ Сообщение отредактировано (user_id: {user_id}, msg_id: {last_message_id})")
                    return edited_message
                except TelegramBadRequest as e:
                    # Сообщение уже удалено или другая ошибка
                    logger.debug(f"⚠️ Не удалось отредактировать сообщение: {e}")
                    # Сбрасываем ID и отправляем новое сообщение
                    reset_last_message_id(user_id)
                    pass
        
        # Отправляем новое сообщение
        sent_message = await message.answer(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )
        
        # Сохраняем ID нового сообщения
        set_last_message_id(user_id, sent_message.message_id)
        logger.debug(f"📤 Новое сообщение отправлено (user_id: {user_id}, msg_id: {sent_message.message_id})")
        
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


async def delete_message(message: types.Message, message_id: Optional[int] = None) -> bool:
    """
    Удалить сообщение
    
    Args:
        message: Объект сообщения из обработчика
        message_id: ID сообщения для удаления (если None, удаляет текущее)
    
    Returns:
        True если удалено успешно, False в противном случае
    """
    try:
        target_message_id = message_id or message.message_id
        user_id = message.from_user.id
        
        await message.bot.delete_message(
            chat_id=user_id,
            message_id=target_message_id
        )
        
        logger.debug(f"🗑️ Сообщение удалено (user_id: {user_id}, msg_id: {target_message_id})")
        return True
        
    except Exception as e:
        logger.debug(f"⚠️ Не удалось удалить сообщение: {e}")
        return False


async def clear_user_messages(user_id: int) -> None:
    """Очистить кэш сообщений пользователя"""
    reset_last_message_id(user_id)
    logger.debug(f"✨ Кэш сообщений очищен для пользователя {user_id}")
