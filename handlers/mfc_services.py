"""
Обработчики для услуг МФЦ - единый модуль
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from utils.logger import logger

router = Router()

# Загрузка данных МФЦ услуг
MFC_DATA_PATH = Path(__file__).parent.parent / "docs" / "mfc_services.json"

def load_mfc_data():
    """Загрузка данных МФЦ услуг из JSON"""
    try:
        with open(MFC_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные МФЦ услуг успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных МФЦ: {e}")
        return None

# Глобальная переменная для хранения данных
mfc_services = None

async def init_mfc_data():
    """Инициализация данных МФЦ"""
    global mfc_services
    mfc_services = load_mfc_data()

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_categories_list():
    """Получить список категорий"""
    if not mfc_services:
        return []
    return mfc_services.get("categories", [])

def get_category_by_index(cat_index):
    """Получить категорию по индексу"""
    categories = get_categories_list()
    if 0 <= cat_index < len(categories):
        return categories[cat_index]
    return None

def get_service_by_index(cat_index, svc_index):
    """Получить услугу по индексам категории и услуги"""
    category = get_category_by_index(cat_index)
    if not category:
        return None
    services = category.get("services", [])
    if 0 <= svc_index < len(services):
        return services[svc_index]
    return None

def format_service_details(service):
    """Форматирование детальной информации об услуге"""
    text = f"📋 <b>{service['name']}</b>\n\n"
    
    # Личное посещение
    if service.get("personal_visit"):
        pv = service["personal_visit"]
        text += "👤 <b>Личное посещение:</b>\n"
        text += f"⏱️ <i>Срок:</i> {pv.get('terms', 'не указан')}\n"
        text += f"📋 <i>Процедура:</i>\n{pv.get('procedure', 'не указана')}\n"
        if pv.get('documents'):
            text += f"📄 <i>Документы:</i> {pv.get('documents')}\n"
        text += "\n"
    else:
        text += "👤 <b>Личное посещение:</b> <i>Недоступно</i>\n\n"
    
    # Электронная услуга
    if service.get("online_service"):
        os = service["online_service"]
        text += "💻 <b>Электронная услуга:</b>\n"
        text += f"⏱️ <i>Срок:</i> {os.get('terms', 'не указан')}\n"
        text += f"📋 <i>Процедура:</i>\n{os.get('procedure', 'не указана')}\n"
        if os.get('documents'):
            text += f"📄 <i>Документы:</i> {os.get('documents')}\n"
    else:
        text += "💻 <b>Электронная услуга:</b> <i>Недоступно</i>\n"
    
    return text

def get_categories_keyboard():
    """Создание inline-клавиатуры с категориями"""
    categories = get_categories_list()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, category in enumerate(categories):
        btn = InlineKeyboardButton(
            text=category["name"],
            callback_data=f"mfc_cat_{i}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")
    ])
    
    return keyboard

def get_services_keyboard(cat_index):
    """Создание inline-клавиатуры с услугами категории"""
    category = get_category_by_index(cat_index)
    if not category:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К категориям", callback_data="mfc_back_to_categories")],
            [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")],
        ])
    
    services = category.get("services", [])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for svc_idx, service in enumerate(services):
        btn = InlineKeyboardButton(
            text=service["name"],
            callback_data=f"mfc_service_{cat_index}_{svc_idx}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 К категориям", callback_data="mfc_back_to_categories")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")
    ])
    
    return keyboard

def get_service_detail_keyboard(cat_index):
    """Создание inline-клавиатуры для деталей услуги"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку услуг", callback_data=f"mfc_back_to_services_{cat_index}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data="mfc_back_to_categories")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")],
    ])

# ============= ОБРАБОТЧИКИ =============

@router.message(F.text == "📋 Услуги МФЦ")
async def handle_mfc_services(message: types.Message):
    """Начало работы с услугами МФЦ - показ категорий"""
    if not mfc_services:
        await init_mfc_data()
    
    if not mfc_services:
        await message.answer("❌ Услуги МФЦ временно недоступны")
        return
    
    text = "📋 **Услуги МФЦ**\n\nВыбери категорию услуг:"
    keyboard = get_categories_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "📚 Студенту")
async def handle_student_menu(message: types.Message):
    """Обработчик для студентов - с кнопкой МФЦ"""
    student_text = "📚 **Информация для студентов**\n\nЗдесь ты найдешь всё что нужно для учёбы и жизни в университете.\n\nВыбери интересующий раздел:"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание занятий")],
            [KeyboardButton(text="📋 Услуги МФЦ")],
            [KeyboardButton(text="💰 Стипендии")],
            [KeyboardButton(text="🏘️ Общежития")],
            [KeyboardButton(text="📚 Студенческие Проекты")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True
    )
    await message.answer(student_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("mfc_cat_"))
async def handle_category_select(callback: types.CallbackQuery):
    """Обработчик выбора категории - показ услуг"""
    try:
        cat_index = int(callback.data.replace("mfc_cat_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка выбора категории", show_alert=True)
        return
    
    category = get_category_by_index(cat_index)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"{category['name']}\n\nВыбери услугу:"
    keyboard = get_services_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("mfc_service_"))
async def handle_service_select(callback: types.CallbackQuery):
    """Обработчик выбора услуги - показ деталей"""
    try:
        data = callback.data.replace("mfc_service_", "")
        cat_index, svc_index = map(int, data.split("_"))
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора услуги", show_alert=True)
        return
    
    service = get_service_by_index(cat_index, svc_index)
    if not service:
        await callback.answer("❌ Услуга не найдена", show_alert=True)
        return
    
    text = format_service_details(service)
    keyboard = get_service_detail_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "mfc_back_to_categories")
async def handle_back_to_categories(callback: types.CallbackQuery):
    """Возврат к списку категорий"""
    if not mfc_services:
        await init_mfc_data()
    
    text = "📋 **Услуги МФЦ**\n\nВыбери категорию услуг:"
    keyboard = get_categories_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("mfc_back_to_services_"))
async def handle_back_to_services(callback: types.CallbackQuery):
    """Возврат к списку услуг категории"""
    try:
        cat_index = int(callback.data.replace("mfc_back_to_services_", ""))
    except ValueError:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    category = get_category_by_index(cat_index)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"{category['name']}\n\nВыбери услугу:"
    keyboard = get_services_keyboard(cat_index)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "mfc_back_to_menu")
async def handle_back_to_menu(callback: types.CallbackQuery):
    """Возврат в раздел студента"""
    student_text = "📚 **Информация для студентов**\n\nЗдесь ты найдешь всё что нужно для учёбы и жизни в университете.\n\nВыбери интересующий раздел:"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание занятий")],
            [KeyboardButton(text="📋 Услуги МФЦ")],
            [KeyboardButton(text="💰 Стипендии")],
            [KeyboardButton(text="🏘️ Общежития")],
            [KeyboardButton(text="📚 Студенческие Проекты")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(student_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
