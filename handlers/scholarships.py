"""
Обработчики для стипендий - единый модуль
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from utils.logger import logger
from utils.message_manager import send_or_edit_message, reset_last_message_id

router = Router()

# Загрузка данных о стипендиях
SCHOLARSHIPS_DATA_PATH = Path(__file__).parent.parent / "docs" / "scholarships.json"

def load_scholarships_data():
    """Загрузка данных о стипендиях из JSON"""
    try:
        with open(SCHOLARSHIPS_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные о стипендиях успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных о стипендиях: {e}")
        return None

# Глобальная переменная для хранения данных
scholarships_data = None

async def init_scholarships_data():
    """Инициализация данных о стипендиях"""
    global scholarships_data
    scholarships_data = load_scholarships_data()

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_categories_list():
    """Получить список категорий стипендий"""
    if not scholarships_data:
        return []
    return scholarships_data.get("categories", [])

def get_category_by_index(cat_index):
    """Получить категорию по индексу"""
    categories = get_categories_list()
    if 0 <= cat_index < len(categories):
        return categories[cat_index]
    return None

def get_scholarship_by_index(cat_index, sch_index):
    """Получить стипендию по индексам категории и стипендии"""
    category = get_category_by_index(cat_index)
    if not category:
        return None
    scholarships = category.get("scholarships", [])
    if 0 <= sch_index < len(scholarships):
        return scholarships[sch_index]
    return None

def format_scholarship_details(scholarship):
    """Форматирование детальной информации о стипендии"""
    text = f"💰 <b>{scholarship['name']}</b>\n\n"
    
    # Описание для кого
    if scholarship.get("recipients"):
        text += f"👥 <b>Для кого:</b>\n{scholarship['recipients']}\n\n"
    
    # Размер
    if scholarship.get("amount"):
        text += f"💵 <b>Размер:</b> {scholarship['amount']}\n"
    
    if scholarship.get("amount_details"):
        text += "<b>Размер по условиям:</b>\n"
        for detail in scholarship['amount_details']:
            text += f"  • {detail.get('condition', 'N/A')}: <b>{detail.get('amount', 'N/A')}</b>\n"
        text += "\n"
    
    if scholarship.get("base_amount"):
        text += f"💵 <b>Базовый размер:</b> {scholarship['base_amount']}\n"
        if scholarship.get("increased_amount"):
            inc = scholarship["increased_amount"]
            text += f"💵 <b>Повышенный размер:</b>\n"
            text += f"  Условие: {inc.get('condition', 'N/A')}\n"
            text += f"  Сумма: <b>{inc.get('amount', 'N/A')}</b>\n"
        text += "\n"
    
    # Периодичность
    if scholarship.get("period"):
        text += f"📅 <b>Периодичность:</b> {scholarship['period']}\n"
    
    # Повышенные размеры
    if scholarship.get("increased_amounts"):
        inc_data = scholarship["increased_amounts"]
        text += f"<b>Повышенные размеры:</b>\n"
        text += f"<i>{inc_data.get('description', '')}</i>\n"
        for detail in inc_data.get('details', []):
            text += f"  • {detail.get('condition', 'N/A')}: <b>{detail.get('amount', 'N/A')}</b>\n"
        text += "\n"
    
    # Для иностранных студентов
    if scholarship.get("foreign_students"):
        fs = scholarship["foreign_students"]
        text += f"🌍 <b>Для иностранных студентов:</b>\n"
        text += f"<i>{fs.get('description', '')}</i>\n"
        text += f"Размер: <b>{fs.get('amount', 'N/A')}</b>\n\n"
    
    # Условия
    if scholarship.get("conditions"):
        text += f"✅ <b>Условия:</b> {scholarship['conditions']}\n"
    
    # Дата начала
    if scholarship.get("start_date"):
        text += f"📌 <b>Начало:</b> {scholarship['start_date']}\n"
    
    # Примечание
    if scholarship.get("note"):
        text += f"📝 <b>Примечание:</b> {scholarship['note']}\n"
    
    return text

def get_categories_keyboard():
    """Создание inline-клавиатуры с категориями стипендий"""
    categories = get_categories_list()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, category in enumerate(categories):
        btn = InlineKeyboardButton(
            text=category["name"],
            callback_data=f"sch_cat_{i}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")
    ])
    
    return keyboard

def get_scholarships_keyboard(cat_index):
    """Создание inline-клавиатуры со стипендиями категории"""
    category = get_category_by_index(cat_index)
    if not category:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К категориям", callback_data="sch_back_to_categories")],
            [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")],
        ])
    
    scholarships = category.get("scholarships", [])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for sch_idx, scholarship in enumerate(scholarships):
        btn = InlineKeyboardButton(
            text=scholarship["name"],
            callback_data=f"sch_scholarship_{cat_index}_{sch_idx}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 К категориям", callback_data="sch_back_to_categories")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")
    ])
    
    return keyboard

def get_scholarship_detail_keyboard(cat_index):
    """Создание inline-клавиатуры для деталей стипендии"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку стипендий", callback_data=f"sch_back_to_scholarships_{cat_index}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="sch_back_to_categories")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")],
    ])

# ============= ОБРАБОТЧИКИ =============

@router.message(F.text == "💰 Стипендии")
async def handle_scholarships(message: types.Message):
    """Начало работы со стипендиями - показ категорий"""
    logger.info("📌 Нажата кнопка 'Стипендии'")
    
    if not scholarships_data:
        logger.info("⚠️ scholarships_data не загружена, инициализирую...")
        await init_scholarships_data()
    
    if not scholarships_data:
        logger.error("❌ Не удалось загрузить данные о стипендиях")
        await send_or_edit_message(message, "❌ Информация о стипендиях временно недоступна")
        return
    
    logger.info(f"✅ Загружено {len(get_categories_list())} категорий стипендий")
    text = "💰 <b>Стипендии МосПолитеха</b>\n\nВыбери категорию стипендий:"
    keyboard = get_categories_keyboard()
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("sch_cat_"))
async def handle_category_select(callback: types.CallbackQuery):
    """Обработчик выбора категории - показ стипендий"""
    try:
        cat_index = int(callback.data.replace("sch_cat_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка выбора категории", show_alert=True)
        return
    
    category = get_category_by_index(cat_index)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"{category['name']}\n\nВыбери стипендию:"
    keyboard = get_scholarships_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("sch_scholarship_"))
async def handle_scholarship_select(callback: types.CallbackQuery):
    """Обработчик выбора стипендии - показ деталей"""
    try:
        data = callback.data.replace("sch_scholarship_", "")
        cat_index, sch_index = map(int, data.split("_"))
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора стипендии", show_alert=True)
        return
    
    scholarship = get_scholarship_by_index(cat_index, sch_index)
    if not scholarship:
        await callback.answer("❌ Стипендия не найдена", show_alert=True)
        return
    
    text = format_scholarship_details(scholarship)
    keyboard = get_scholarship_detail_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "sch_back_to_categories")
async def handle_back_to_categories(callback: types.CallbackQuery):
    """Возврат к списку категорий"""
    if not scholarships_data:
        await init_scholarships_data()
    
    text = "💰 <b>Стипендии МосПолитеха</b>\n\nВыбери категорию стипендий:"
    keyboard = get_categories_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("sch_back_to_scholarships_"))
async def handle_back_to_scholarships(callback: types.CallbackQuery):
    """Возврат к списку стипендий категории"""
    try:
        cat_index = int(callback.data.replace("sch_back_to_scholarships_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    category = get_category_by_index(cat_index)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"{category['name']}\n\nВыбери стипендию:"
    keyboard = get_scholarships_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "sch_back_to_menu")
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
        resize_keyboard=True
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.edit_text(student_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
"""
Обработчики для стипендий - единый модуль
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from utils.logger import logger
from utils.message_manager import send_or_edit_message, reset_last_message_id

router = Router()

# Загрузка данных о стипендиях
SCHOLARSHIPS_DATA_PATH = Path(__file__).parent.parent / "docs" / "scholarships.json"

def load_scholarships_data():
    """Загрузка данных о стипендиях из JSON"""
    try:
        with open(SCHOLARSHIPS_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные о стипендиях успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных о стипендиях: {e}")
        return None

# Глобальная переменная для хранения данных
scholarships_data = None

async def init_scholarships_data():
    """Инициализация данных о стипендиях"""
    global scholarships_data
    scholarships_data = load_scholarships_data()

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_categories_list():
    """Получить список категорий стипендий"""
    if not scholarships_data:
        return []
    return scholarships_data.get("categories", [])

def get_category_by_index(cat_index):
    """Получить категорию по индексу"""
    categories = get_categories_list()
    if 0 <= cat_index < len(categories):
        return categories[cat_index]
    return None

def get_scholarship_by_index(cat_index, sch_index):
    """Получить стипендию по индексам категории и стипендии"""
    category = get_category_by_index(cat_index)
    if not category:
        return None
    scholarships = category.get("scholarships", [])
    if 0 <= sch_index < len(scholarships):
        return scholarships[sch_index]
    return None

def format_scholarship_details(scholarship):
    """Форматирование детальной информации о стипендии"""
    text = f"💰 <b>{scholarship['name']}</b>\n\n"
    
    # Описание для кого
    if scholarship.get("recipients"):
        text += f"👥 <b>Для кого:</b>\n{scholarship['recipients']}\n\n"
    
    # Размер
    if scholarship.get("amount"):
        text += f"💵 <b>Размер:</b> {scholarship['amount']}\n"
    
    if scholarship.get("amount_details"):
        text += "<b>Размер по условиям:</b>\n"
        for detail in scholarship['amount_details']:
            text += f"  • {detail.get('condition', 'N/A')}: <b>{detail.get('amount', 'N/A')}</b>\n"
        text += "\n"
    
    if scholarship.get("base_amount"):
        text += f"💵 <b>Базовый размер:</b> {scholarship['base_amount']}\n"
        if scholarship.get("increased_amount"):
            inc = scholarship["increased_amount"]
            text += f"💵 <b>Повышенный размер:</b>\n"
            text += f"  Условие: {inc.get('condition', 'N/A')}\n"
            text += f"  Сумма: <b>{inc.get('amount', 'N/A')}</b>\n"
        text += "\n"
    
    # Периодичность
    if scholarship.get("period"):
        text += f"📅 <b>Периодичность:</b> {scholarship['period']}\n"
    
    # Повышенные размеры
    if scholarship.get("increased_amounts"):
        inc_data = scholarship["increased_amounts"]
        text += f"<b>Повышенные размеры:</b>\n"
        text += f"<i>{inc_data.get('description', '')}</i>\n"
        for detail in inc_data.get('details', []):
            text += f"  • {detail.get('condition', 'N/A')}: <b>{detail.get('amount', 'N/A')}</b>\n"
        text += "\n"
    
    # Для иностранных студентов
    if scholarship.get("foreign_students"):
        fs = scholarship["foreign_students"]
        text += f"🌍 <b>Для иностранных студентов:</b>\n"
        text += f"<i>{fs.get('description', '')}</i>\n"
        text += f"Размер: <b>{fs.get('amount', 'N/A')}</b>\n\n"
    
    # Условия
    if scholarship.get("conditions"):
        text += f"✅ <b>Условия:</b> {scholarship['conditions']}\n"
    
    # Дата начала
    if scholarship.get("start_date"):
        text += f"📌 <b>Начало:</b> {scholarship['start_date']}\n"
    
    # Примечание
    if scholarship.get("note"):
        text += f"📝 <b>Примечание:</b> {scholarship['note']}\n"
    
    return text

def get_categories_keyboard():
    """Создание inline-клавиатуры с категориями стипендий"""
    categories = get_categories_list()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, category in enumerate(categories):
        btn = InlineKeyboardButton(
            text=category["name"],
            callback_data=f"sch_cat_{i}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")
    ])
    
    return keyboard

def get_scholarships_keyboard(cat_index):
    """Создание inline-клавиатуры со стипендиями категории"""
    category = get_category_by_index(cat_index)
    if not category:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К категориям", callback_data="sch_back_to_categories")],
            [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")],
        ])
    
    scholarships = category.get("scholarships", [])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for sch_idx, scholarship in enumerate(scholarships):
        btn = InlineKeyboardButton(
            text=scholarship["name"],
            callback_data=f"sch_scholarship_{cat_index}_{sch_idx}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 К категориям", callback_data="sch_back_to_categories")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")
    ])
    
    return keyboard

def get_scholarship_detail_keyboard(cat_index):
    """Создание inline-клавиатуры для деталей стипендии"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку стипендий", callback_data=f"sch_back_to_scholarships_{cat_index}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="sch_back_to_categories")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="sch_back_to_menu")],
    ])

# ============= ОБРАБОТЧИКИ =============

@router.message(F.text == "💰 Стипендии")
async def handle_scholarships(message: types.Message):
    """Начало работы со стипендиями - показ категорий"""
    logger.info("📌 Нажата кнопка 'Стипендии'")
    
    if not scholarships_data:
        logger.info("⚠️ scholarships_data не загружена, инициализирую...")
        await init_scholarships_data()
    
    if not scholarships_data:
        logger.error("❌ Не удалось загрузить данные о стипендиях")
        await send_or_edit_message(message, "❌ Информация о стипендиях временно недоступна")
        return
    
    logger.info(f"✅ Загружено {len(get_categories_list())} категорий стипендий")
    text = "💰 <b>Стипендии МосПолитеха</b>\n\nВыбери категорию стипендий:"
    keyboard = get_categories_keyboard()
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("sch_cat_"))
async def handle_category_select(callback: types.CallbackQuery):
    """Обработчик выбора категории - показ стипендий"""
    try:
        cat_index = int(callback.data.replace("sch_cat_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка выбора категории", show_alert=True)
        return
    
    category = get_category_by_index(cat_index)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"{category['name']}\n\nВыбери стипендию:"
    keyboard = get_scholarships_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("sch_scholarship_"))
async def handle_scholarship_select(callback: types.CallbackQuery):
    """Обработчик выбора стипендии - показ деталей"""
    try:
        data = callback.data.replace("sch_scholarship_", "")
        cat_index, sch_index = map(int, data.split("_"))
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора стипендии", show_alert=True)
        return
    
    scholarship = get_scholarship_by_index(cat_index, sch_index)
    if not scholarship:
        await callback.answer("❌ Стипендия не найдена", show_alert=True)
        return
    
    text = format_scholarship_details(scholarship)
    keyboard = get_scholarship_detail_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "sch_back_to_categories")
async def handle_back_to_categories(callback: types.CallbackQuery):
    """Возврат к списку категорий"""
    if not scholarships_data:
        await init_scholarships_data()
    
    text = "💰 <b>Стипендии МосПолитеха</b>\n\nВыбери категорию стипендий:"
    keyboard = get_categories_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("sch_back_to_scholarships_"))
async def handle_back_to_scholarships(callback: types.CallbackQuery):
    """Возврат к списку стипендий категории"""
    try:
        cat_index = int(callback.data.replace("sch_back_to_scholarships_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    category = get_category_by_index(cat_index)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"{category['name']}\n\nВыбери стипендию:"
    keyboard = get_scholarships_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

