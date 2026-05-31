"""
Централизованный модуль для управления навигацией и клавиатурами
Этот модуль обеспечивает единство навигации во всем боте
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List

# ==================== КОНСТАНТЫ ====================

# Кнопки возврата
BACK_TEXT = "◀️ Назад"
BACK_TO_MENU = "🏠 Главное меню"
BACK_TO_STUDENT = "📚 Студенту"

# Основные разделы главного меню
SECTIONS = {
    "aspirant": "👨‍🎓 Абитуриенту",
    "student": "📚 Студенту",
    "events": "🎪 Мероприятия",
    "contacts": "📞 Контакты",
    "help": "❓ Помощь",
    "feedback": "💬 Обратная связь",
}

# Подразделы для студентов
STUDENT_SECTIONS = {
    "schedule": "📅 Расписание занятий",
    "mfc": "📋 Услуги МФЦ",
    "scholarships": "💰 Стипендии",
    "dormitories": "🏘️ Общежития",
    "projects": "📚 Студенческие Проекты",
    "aspirantura": "🎓 Аспирантура",
    "benefits": "📗 Льготы студентов",
    "library": "📖 Библиотека",
    "events": "🎪 Мероприятия",
    "military": "🎖️ Военнообязанным",
}

# Категории мероприятий
EVENT_CATEGORIES = {
    "education": "🎓 Обучение",
    "careers": "💼 Карьера",
    "competitions": "🏆 Конкурсы",
    "culture": "🎭 Культура",
    "student_life": "🎉 Студенческая жизнь",
    "volunteering": "🤝 Волонтёрство",
}

# ==================== КЛАВИАТУРЫ ГЛАВНОГО МЕНЮ ====================

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Получить клавиатуру главного меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=SECTIONS["aspirant"]),
                KeyboardButton(text=SECTIONS["student"])
            ],
            [
                KeyboardButton(text=SECTIONS["events"]),
                KeyboardButton(text=SECTIONS["contacts"])
            ],
            [
                KeyboardButton(text=SECTIONS["help"]),
                KeyboardButton(text=SECTIONS["feedback"])
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


# ==================== КЛАВИАТУРЫ РАЗДЕЛА АБИТУРИЕНТОВ ====================

def get_aspirant_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура меню абитуриентов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Программы обучения")],
            [KeyboardButton(text="📋 Процесс поступления")],
            [KeyboardButton(text="📞 Контакты приемной комиссии")],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True
    )
    return keyboard


# ==================== КЛАВИАТУРЫ РАЗДЕЛА СТУДЕНТОВ ====================

def get_student_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура меню студентов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=STUDENT_SECTIONS["schedule"])],
            [KeyboardButton(text=STUDENT_SECTIONS["mfc"])],
            [KeyboardButton(text=STUDENT_SECTIONS["scholarships"])],
            [KeyboardButton(text=STUDENT_SECTIONS["dormitories"])],
            [KeyboardButton(text=STUDENT_SECTIONS["projects"])],
            [KeyboardButton(text=STUDENT_SECTIONS["aspirantura"])],
            [KeyboardButton(text=STUDENT_SECTIONS["benefits"])],
            [KeyboardButton(text=STUDENT_SECTIONS["library"])],
            [KeyboardButton(text=STUDENT_SECTIONS["events"])],
            [KeyboardButton(text=STUDENT_SECTIONS["military"])],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True
    )
    return keyboard


# ==================== КЛАВИАТУРЫ МЕРОПРИЯТИЙ ====================

def get_events_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура меню мероприятий"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Все мероприятия")],
            [
                KeyboardButton(text=EVENT_CATEGORIES["education"]),
                KeyboardButton(text=EVENT_CATEGORIES["careers"])
            ],
            [
                KeyboardButton(text=EVENT_CATEGORIES["competitions"]),
                KeyboardButton(text=EVENT_CATEGORIES["culture"])
            ],
            [
                KeyboardButton(text=EVENT_CATEGORIES["student_life"]),
                KeyboardButton(text=EVENT_CATEGORIES["volunteering"])
            ],
            [KeyboardButton(text="🔍 Поиск мероприятия")],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True
    )
    return keyboard


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ INLINE КЛАВИАТУР ====================

def get_back_button(callback_data: str, text: str = "🔙 Назад") -> List[List[InlineKeyboardButton]]:
    """
    Получить кнопку возврата для inline клавиатуры
    
    Args:
        callback_data: Callback data для кнопки
        text: Текст кнопки (по умолчанию "🔙 Назад")
    
    Returns:
        Список со списком кнопок (для добавления в inline_keyboard)
    """
    return [[InlineKeyboardButton(text=text, callback_data=callback_data)]]


def get_back_to_menu_button(callback_data: str = "back_to_main_menu") -> List[List[InlineKeyboardButton]]:
    """
    Получить кнопку возврата в главное меню
    
    Args:
        callback_data: Callback data для кнопки (по умолчанию "back_to_main_menu")
    
    Returns:
        Список со списком кнопок
    """
    return [[InlineKeyboardButton(text="🏠 Главное меню", callback_data=callback_data)]]


def add_navigation_buttons(
    keyboard: InlineKeyboardMarkup,
    back_callback: str,
    menu_callback: str = "back_to_main_menu"
) -> InlineKeyboardMarkup:
    """
    Добавить кнопки навигации к существующей inline-клавиатуре
    
    Args:
        keyboard: Существующая inline-клавиатура
        back_callback: Callback для кнопки "Назад"
        menu_callback: Callback для кнопки "Главное меню"
    
    Returns:
        Обновленная клавиатура
    """
    keyboard.inline_keyboard.extend(get_back_button(back_callback))
    keyboard.inline_keyboard.extend(get_back_to_menu_button(menu_callback))
    return keyboard


# ==================== CALLBACK HANDLERS ====================

# Единые callback_data для всех модулей
CALLBACKS = {
    # Основная навигация
    "back_to_main_menu": "back_to_main_menu",
    "back_to_student_menu": "back_to_student_menu",
    
    # Мероприятия
    "back_to_events_menu": "back_to_events_menu",
    
    # Другие модули используют свои префиксы, но все они должны
    # поддерживать обработчик "back_to_main_menu"
}


def is_back_to_main_menu(callback_data: str) -> bool:
    """Проверить, является ли callback возвратом в главное меню"""
    return callback_data == CALLBACKS["back_to_main_menu"]


def is_back_to_student_menu(callback_data: str) -> bool:
    """Проверить, является ли callback возвратом в меню студента"""
    return callback_data == CALLBACKS["back_to_student_menu"]


def is_back_to_events_menu(callback_data: str) -> bool:
    """Проверить, является ли callback возвратом в меню мероприятий"""
    return callback_data == CALLBACKS["back_to_events_menu"]
