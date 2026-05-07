"""
Утилиты для работы с клавиатурой и сообщениями
Централизует создание кнопок и клавиатур для уменьшения дублирования кода
"""

from typing import List, Optional, Union
from aiogram.types import (
    ReplyKeyboardMarkup, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    KeyboardButton
)
from utils.logger import logger


class KeyboardBuilder:
    """Построитель клавиатур для уменьшения дублирования кода"""
    
    @staticmethod
    def create_reply_keyboard(
        buttons: List[Union[str, List[str]]],
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        selective: bool = False
    ) -> ReplyKeyboardMarkup:
        """
        Создать клавиатуру ответов
        
        Args:
            buttons: Список кнопок или список списков кнопок (для рядов)
            resize_keyboard: Подогнать под экран
            one_time_keyboard: Скрывать после нажатия
            selective: Показывать только указанным пользователям
            
        Returns:
            ReplyKeyboardMarkup
        """
        try:
            keyboard_buttons = []
            
            for row in buttons:
                if isinstance(row, str):
                    # Одна кнопка в ряду
                    keyboard_buttons.append([KeyboardButton(text=row)])
                elif isinstance(row, list):
                    # Несколько кнопок в ряду
                    keyboard_buttons.append([KeyboardButton(text=btn) for btn in row])
            
            return ReplyKeyboardMarkup(
                keyboard=keyboard_buttons,
                resize_keyboard=resize_keyboard,
                one_time_keyboard=one_time_keyboard,
                selective=selective
            )
        except Exception as e:
            logger.error(f"Ошибка при создании reply клавиатуры: {e}")
            # Возвращаем простую клавиатуру по умолчанию
            return ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Главное меню")]],
                resize_keyboard=True
            )
    
    @staticmethod
    def create_inline_keyboard(
        buttons: List[tuple[str, str]],
        items_per_row: int = 2
    ) -> InlineKeyboardMarkup:
        """
        Создать inline клавиатуру
        
        Args:
            buttons: Список кортежей (текст, callback_data)
            items_per_row: Количество кнопок в ряду
            
        Returns:
            InlineKeyboardMarkup
        """
        try:
            keyboard_buttons = []
            row = []
            
            for text, callback_data in buttons:
                row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
                
                if len(row) == items_per_row:
                    keyboard_buttons.append(row)
                    row = []
            
            if row:  # Добавить оставшиеся кнопки
                keyboard_buttons.append(row)
            
            return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        except Exception as e:
            logger.error(f"Ошибка при создании inline клавиатуры: {e}")
            return InlineKeyboardMarkup(inline_keyboard=[])
    
    @staticmethod
    def add_back_button(
        keyboard: ReplyKeyboardMarkup,
        back_text: str = "◀️ Назад"
    ) -> ReplyKeyboardMarkup:
        """
        Добавить кнопку "Назад" в конец клавиатуры
        
        Args:
            keyboard: Существующая клавиатура
            back_text: Текст кнопки
            
        Returns:
            Обновленная клавиатура
        """
        try:
            kb_list = list(keyboard.keyboard)
            kb_list.append([KeyboardButton(text=back_text)])
            
            return ReplyKeyboardMarkup(
                keyboard=kb_list,
                resize_keyboard=keyboard.resize_keyboard,
                one_time_keyboard=keyboard.one_time_keyboard,
                selective=keyboard.selective
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении кнопки 'Назад': {e}")
            return keyboard


class MessageFormatter:
    """Форматтер сообщений для единого стиля"""
    
    # Эмодзи для разных типов сообщений
    EMOJI = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'loading': '⏳',
        'back': '◀️',
        'menu': '📋',
        'schedule': '📅',
        'search': '🔍',
        'star': '⭐',
        'heart': '❤️',
        'clock': '🕐',
    }
    
    @staticmethod
    def format_error(message: str, hint: Optional[str] = None) -> str:
        """
        Форматировать сообщение об ошибке
        
        Args:
            message: Текст ошибки
            hint: Подсказка для пользователя
            
        Returns:
            Форматированное сообщение
        """
        text = f"{MessageFormatter.EMOJI['error']} <b>Ошибка</b>\n\n{message}"
        
        if hint:
            text += f"\n\n💡 <u>Подсказка:</u>\n{hint}"
        
        return text
    
    @staticmethod
    def format_success(message: str) -> str:
        """Форматировать сообщение об успехе"""
        return f"{MessageFormatter.EMOJI['success']} <b>Успешно</b>\n\n{message}"
    
    @staticmethod
    def format_info(title: str, content: str, footer: Optional[str] = None) -> str:
        """Форматировать информационное сообщение"""
        text = f"{MessageFormatter.EMOJI['info']} <b>{title}</b>\n\n{content}"
        
        if footer:
            text += f"\n\n<i>{footer}</i>"
        
        return text
    
    @staticmethod
    def format_list(title: str, items: List[str], max_items: Optional[int] = None) -> str:
        """
        Форматировать список
        
        Args:
            title: Заголовок списка
            items: Элементы списка
            max_items: Максимальное количество элементов для показа
            
        Returns:
            Форматированный список
        """
        if max_items:
            items = items[:max_items]
        
        text = f"<b>{title}</b>\n\n"
        for i, item in enumerate(items, 1):
            text += f"{i}. {item}\n"
        
        return text.strip()
    
    @staticmethod
    def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
        """
        Обрезать текст до максимальной длины
        
        Args:
            text: Текст для обрезания
            max_length: Максимальная длина
            suffix: Суффикс для обрезанного текста
            
        Returns:
            Обрезанный текст
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix


class ValidationMessages:
    """Сообщения для валидации входных данных"""
    
    @staticmethod
    def empty_input() -> str:
        """Сообщение при пустом вводе"""
        return f"{MessageFormatter.EMOJI['error']} Ввод не может быть пустым"
    
    @staticmethod
    def invalid_format(expected: str) -> str:
        """Сообщение при неверном формате"""
        return f"{MessageFormatter.EMOJI['error']} Неверный формат. Ожидается: {expected}"
    
    @staticmethod
    def too_long(max_length: int) -> str:
        """Сообщение при переполнении длины"""
        return f"{MessageFormatter.EMOJI['error']} Текст слишком длинный (максимум {max_length} символов)"
    
    @staticmethod
    def too_short(min_length: int) -> str:
        """Сообщение при недостаточной длине"""
        return f"{MessageFormatter.EMOJI['error']} Текст слишком короткий (минимум {min_length} символов)"
    
    @staticmethod
    def not_found(item_type: str) -> str:
        """Сообщение при отсутствии результатов"""
        return f"{MessageFormatter.EMOJI['info']} {item_type} не найден(а)"
    
    @staticmethod
    def try_again() -> str:
        """Сообщение для повторной попытки"""
        return f"{MessageFormatter.EMOJI['warning']} Пожалуйста, попробуйте еще раз"
