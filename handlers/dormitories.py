"""
Обработчики для общежитий
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from utils.logger import logger
from utils.message_manager import send_or_edit_message, reset_last_message_id

router = Router()

# Загрузка данных об общежитиях
DORMITORIES_DATA_PATH = Path(__file__).parent.parent / "docs" / "dormitories.json"

def load_dormitories_data():
    """Загрузка данных об общежитиях из JSON"""
    try:
        with open(DORMITORIES_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные об общежитиях успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных об общежитиях: {e}")
        return None

# Глобальная переменная для хранения данных
dormitories_data = None

async def init_dormitories_data():
    """Инициализация данных об общежитиях"""
    global dormitories_data
    dormitories_data = load_dormitories_data()

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_dormitories_list():
    """Получить список всех общежитий"""
    if not dormitories_data:
        return []
    return dormitories_data.get("dormitories", [])

def get_dormitory_by_index(dorm_index):
    """Получить общежитие по индексу"""
    dormitories = get_dormitories_list()
    if 0 <= dorm_index < len(dormitories):
        return dormitories[dorm_index]
    return None

def format_dormitory_details(dormitory):
    """Форматирование детальной информации об общежитии"""
    text = f"🏘️ <b>{dormitory['name']}</b>\n\n"
    
    # Адрес
    if dormitory.get("address"):
        text += f"📍 <b>Адрес:</b> {dormitory['address']}\n\n"
    
    # Тип общежития
    if dormitory.get("type"):
        text += f"🏠 <b>Тип:</b> {dormitory['type'].capitalize()}\n"
    
    # Описание комнат
    if dormitory.get("rooms_description"):
        text += f"🛏️ <b>Типы комнат:</b> {dormitory['rooms_description']}\n"
    
    # Вместимость
    if dormitory.get("capacity"):
        text += f"👥 <b>Вместимость:</b> {dormitory['capacity']}\n\n"
    
    # Инфраструктура
    if dormitory.get("infrastructure"):
        text += f"🏢 <b>Инфраструктура:</b>\n"
        for item in dormitory["infrastructure"]:
            text += f"  • {item}\n"
        text += "\n"
    
    # Базовые цены
    if dormitory.get("prices", {}).get("basic"):
        text += f"💰 <b>Базовые цены на проживание:</b>\n"
        basic = dormitory["prices"]["basic"]
        if basic.get("bachelor_specialist_master"):
            text += f"  • Бакалавриат/Магистратура: <b>{basic['bachelor_specialist_master']} руб.</b>\n"
        if basic.get("postgraduate"):
            text += f"  • Аспирантура: <b>{basic['postgraduate']} руб.</b>\n"
        if basic.get("extramural_per_day"):
            text += f"  • Заочная (в сутки): <b>{basic['extramural_per_day']} руб.</b>\n"
        text += "\n"
    
    # Контрактные цены
    if dormitory.get("prices", {}).get("contract"):
        text += f"💳 <b>Контрактные цены:</b>\n"
        contract = dormitory["prices"]["contract"]
        if contract.get("fulltime"):
            text += f"  • Очная форма: <b>{contract['fulltime']} руб.</b>\n"
        if contract.get("fpc_per_day"):
            text += f"  • ФПК (в сутки): <b>{contract['fpc_per_day']} руб.</b>\n"
        if contract.get("extramural_per_day"):
            text += f"  • Заочная (в сутки): <b>{contract['extramural_per_day']} руб.</b>\n"
    
    return text

def get_dormitories_keyboard():
    """Создание inline-клавиатуры со списком общежитий"""
    dormitories = get_dormitories_list()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, dorm in enumerate(dormitories):
        btn = InlineKeyboardButton(
            text=dorm["name"],
            callback_data=f"dorm_select_{i}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="dorm_back_to_menu")
    ])
    
    return keyboard

def get_dormitory_detail_keyboard():
    """Создание inline-клавиатуры для деталей общежития"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку общежитий", callback_data="dorm_back_to_list")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="dorm_back_to_menu")],
    ])

# ============= ОБРАБОТЧИКИ =============

@router.message(F.text == "🏘️ Общежития")
async def handle_dormitories(message: types.Message):
    """Начало работы с общежитиями - показ списка"""
    logger.info("📌 Нажата кнопка 'Общежития'")
    
    if not dormitories_data:
        logger.info("⚠️ dormitories_data не загружена, инициализирую...")
        await init_dormitories_data()
    
    if not dormitories_data:
        logger.error("❌ Не удалось загрузить данные об общежитиях")
        await send_or_edit_message(message, "❌ Информация об общежитиях временно недоступна")
        return
    
    # Показываем общую информацию
    general_info = dormitories_data.get("general_info", {})
    text = f"🏘️ <b>{general_info.get('title', 'Студенческие общежития')}</b>\n\n"
    text += f"{general_info.get('description', '')}\n\n"
    text += f"<b>Выбери общежитие для подробной информации:</b>"
    
    keyboard = get_dormitories_keyboard()
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("dorm_select_"))
async def handle_dormitory_select(callback: types.CallbackQuery):
    """Обработчик выбора общежития - показ деталей"""
    try:
        dorm_index = int(callback.data.replace("dorm_select_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка выбора общежития", show_alert=True)
        return
    
    dormitory = get_dormitory_by_index(dorm_index)
    if not dormitory:
        await callback.answer("❌ Общежитие не найдено", show_alert=True)
        return
    
    text = format_dormitory_details(dormitory)
    keyboard = get_dormitory_detail_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "dorm_back_to_list")
async def handle_back_to_list(callback: types.CallbackQuery):
    """Возврат к списку общежитий"""
    if not dormitories_data:
        await init_dormitories_data()
    
    general_info = dormitories_data.get("general_info", {})
    text = f"🏘️ <b>{general_info.get('title', 'Студенческие общежития')}</b>\n\n"
    text += f"{general_info.get('description', '')}\n\n"
    text += f"<b>Выбери общежитие для подробной информации:</b>"
    
    keyboard = get_dormitories_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "dorm_back_to_menu")
async def handle_back_to_menu(callback: types.CallbackQuery):
    """Возврат в раздел студента"""
    student_text = "📚 <b>Информация для студентов</b>\n\nЗдесь ты найдешь всё что нужно для учёбы и жизни в университете.\n\nВыбери интересующий раздел:"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание занятий")],
            [KeyboardButton(text="📋 Услуги МФЦ")],
            [KeyboardButton(text="💰 Стипендии")],
            [KeyboardButton(text="🏘️ Общежития")],
            [KeyboardButton(text="📚 Студенческие Проекты")],
            [KeyboardButton(text="📖 Библиотека")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.chat.send_message(student_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
"""
Обработчики для общежитий
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from utils.logger import logger
from utils.message_manager import send_or_edit_message, reset_last_message_id

router = Router()

# Загрузка данных об общежитиях
DORMITORIES_DATA_PATH = Path(__file__).parent.parent / "docs" / "dormitories.json"

def load_dormitories_data():
    """Загрузка данных об общежитиях из JSON"""
    try:
        with open(DORMITORIES_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные об общежитиях успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных об общежитиях: {e}")
        return None

# Глобальная переменная для хранения данных
dormitories_data = None

async def init_dormitories_data():
    """Инициализация данных об общежитиях"""
    global dormitories_data
    dormitories_data = load_dormitories_data()

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_dormitories_list():
    """Получить список всех общежитий"""
    if not dormitories_data:
        return []
    return dormitories_data.get("dormitories", [])

def get_dormitory_by_index(dorm_index):
    """Получить общежитие по индексу"""
    dormitories = get_dormitories_list()
    if 0 <= dorm_index < len(dormitories):
        return dormitories[dorm_index]
    return None

def format_dormitory_details(dormitory):
    """Форматирование детальной информации об общежитии"""
    text = f"🏘️ <b>{dormitory['name']}</b>\n\n"
    
    # Адрес
    if dormitory.get("address"):
        text += f"📍 <b>Адрес:</b> {dormitory['address']}\n\n"
    
    # Тип общежития
    if dormitory.get("type"):
        text += f"🏠 <b>Тип:</b> {dormitory['type'].capitalize()}\n"
    
    # Описание комнат
    if dormitory.get("rooms_description"):
        text += f"🛏️ <b>Типы комнат:</b> {dormitory['rooms_description']}\n"
    
    # Вместимость
    if dormitory.get("capacity"):
        text += f"👥 <b>Вместимость:</b> {dormitory['capacity']}\n\n"
    
    # Инфраструктура
    if dormitory.get("infrastructure"):
        text += f"🏢 <b>Инфраструктура:</b>\n"
        for item in dormitory["infrastructure"]:
            text += f"  • {item}\n"
        text += "\n"
    
    # Базовые цены
    if dormitory.get("prices", {}).get("basic"):
        text += f"💰 <b>Базовые цены на проживание:</b>\n"
        basic = dormitory["prices"]["basic"]
        if basic.get("bachelor_specialist_master"):
            text += f"  • Бакалавриат/Магистратура: <b>{basic['bachelor_specialist_master']} руб.</b>\n"
        if basic.get("postgraduate"):
            text += f"  • Аспирантура: <b>{basic['postgraduate']} руб.</b>\n"
        if basic.get("extramural_per_day"):
            text += f"  • Заочная (в сутки): <b>{basic['extramural_per_day']} руб.</b>\n"
        text += "\n"
    
    # Контрактные цены
    if dormitory.get("prices", {}).get("contract"):
        text += f"💳 <b>Контрактные цены:</b>\n"
        contract = dormitory["prices"]["contract"]
        if contract.get("fulltime"):
            text += f"  • Очная форма: <b>{contract['fulltime']} руб.</b>\n"
        if contract.get("fpc_per_day"):
            text += f"  • ФПК (в сутки): <b>{contract['fpc_per_day']} руб.</b>\n"
        if contract.get("extramural_per_day"):
            text += f"  • Заочная (в сутки): <b>{contract['extramural_per_day']} руб.</b>\n"
    
    return text

def get_dormitories_keyboard():
    """Создание inline-клавиатуры со списком общежитий"""
    dormitories = get_dormitories_list()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, dorm in enumerate(dormitories):
        btn = InlineKeyboardButton(
            text=dorm["name"],
            callback_data=f"dorm_select_{i}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="dorm_back_to_menu")
    ])
    
    return keyboard

def get_dormitory_detail_keyboard():
    """Создание inline-клавиатуры для деталей общежития"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку общежитий", callback_data="dorm_back_to_list")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="dorm_back_to_menu")],
    ])

# ============= ОБРАБОТЧИКИ =============

@router.message(F.text == "🏘️ Общежития")
async def handle_dormitories(message: types.Message):
    """Начало работы с общежитиями - показ списка"""
    logger.info("📌 Нажата кнопка 'Общежития'")
    
    if not dormitories_data:
        logger.info("⚠️ dormitories_data не загружена, инициализирую...")
        await init_dormitories_data()
    
    if not dormitories_data:
        logger.error("❌ Не удалось загрузить данные об общежитиях")
        await send_or_edit_message(message, "❌ Информация об общежитиях временно недоступна")
        return
    
    # Показываем общую информацию
    general_info = dormitories_data.get("general_info", {})
    text = f"🏘️ <b>{general_info.get('title', 'Студенческие общежития')}</b>\n\n"
    text += f"{general_info.get('description', '')}\n\n"
    text += f"<b>Выбери общежитие для подробной информации:</b>"
    
    keyboard = get_dormitories_keyboard()
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("dorm_select_"))
async def handle_dormitory_select(callback: types.CallbackQuery):
    """Обработчик выбора общежития - показ деталей"""
    try:
        dorm_index = int(callback.data.replace("dorm_select_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка выбора общежития", show_alert=True)
        return
    
    dormitory = get_dormitory_by_index(dorm_index)
    if not dormitory:
        await callback.answer("❌ Общежитие не найдено", show_alert=True)
        return
    
    text = format_dormitory_details(dormitory)
    keyboard = get_dormitory_detail_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "dorm_back_to_list")
async def handle_back_to_list(callback: types.CallbackQuery):
    """Возврат к списку общежитий"""
    if not dormitories_data:
        await init_dormitories_data()
    
    general_info = dormitories_data.get("general_info", {})
    text = f"🏘️ <b>{general_info.get('title', 'Студенческие общежития')}</b>\n\n"
    text += f"{general_info.get('description', '')}\n\n"
    text += f"<b>Выбери общежитие для подробной информации:</b>"
    
    keyboard = get_dormitories_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "dorm_back_to_menu")
async def handle_back_to_menu(callback: types.CallbackQuery):
    """Возврат в раздел студента"""
    student_text = "📚 <b>Информация для студентов</b>\n\nЗдесь ты найдешь всё что нужно для учёбы и жизни в университете.\n\nВыбери интересующий раздел:"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание занятий")],
            [KeyboardButton(text="📋 Услуги МФЦ")],
            [KeyboardButton(text="💰 Стипендии")],
            [KeyboardButton(text="🏘️ Общежития")],
            [KeyboardButton(text="📚 Студенческие Проекты")],
            [KeyboardButton(text="📖 Библиотека")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.chat.send_message(student_text, reply_markup=keyboard, parse_mode="HTML")
