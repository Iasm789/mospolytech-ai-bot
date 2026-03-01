"""
Обработчики для услуг МФЦ - единый модуль
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from utils.logger import logger
from utils.message_manager import send_or_edit_message, reset_last_message_id

router = Router()

# Загрузка данных МФЦ услуг
MFC_DATA_PATH = Path(__file__).parent.parent / "docs" / "mfc_services.json"
MFC_OLD_DATA_PATH = Path(__file__).parent.parent / "docs" / "mfc_old_services.json"

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

def load_mfc_old_data():
    """Загрузка данных МФЦ услуг для ранее обучавшихся из JSON"""
    try:
        with open(MFC_OLD_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные МФЦ услуг для ранее обучавшихся успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке старых данных МФЦ: {e}")
        return None

# Глобальные переменные для хранения данных
mfc_services = None
mfc_old_services = None

async def init_mfc_data():
    """Инициализация данных МФЦ"""
    global mfc_services, mfc_old_services
    mfc_services = load_mfc_data()
    mfc_old_services = load_mfc_old_data()

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_categories_list(mode="current"):
    """Получить список категорий
    
    Args:
        mode: "current" для текущих студентов, "old" для ранее обучавшихся
    """
    if mode == "current":
        if not mfc_services:
            return []
        return mfc_services.get("categories", [])
    elif mode == "old":
        if not mfc_old_services:
            return []
        return mfc_old_services.get("categories", [])
    return []

def get_category_by_index(cat_index, mode="current"):
    """Получить категорию по индексу"""
    categories = get_categories_list(mode)
    if 0 <= cat_index < len(categories):
        return categories[cat_index]
    return None

def get_service_by_index(cat_index, svc_index, mode="current"):
    """Получить услугу по индексам категории и услуги"""
    category = get_category_by_index(cat_index, mode)
    if not category:
        return None
    services = category.get("services", [])
    if 0 <= svc_index < len(services):
        return services[svc_index]
    return None

def format_service_details(service):
    """Форматирование детальной информации об услуге"""
    text = f"📋 <b>{service['name']}</b>\n\n"
    
    # Формат новых услуг (с personal_visit и online_service объектами)
    if service.get("personal_visit") or service.get("online_service"):
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
    else:
        # Формат старых услуг (с terms_personal, procedure_personal, etc.)
        has_personal = service.get("terms_personal") or service.get("procedure_personal")
        has_online = service.get("terms_online") or service.get("procedure_online")
        
        if has_personal:
            text += "👤 <b>Личное посещение:</b>\n"
            if service.get("terms_personal"):
                text += f"⏱️ <i>Срок:</i> {service.get('terms_personal')}\n"
            if service.get("procedure_personal"):
                text += f"📋 <i>Процедура:</i>\n{service.get('procedure_personal')}\n"
            text += "\n"
        
        if has_online:
            text += "💻 <b>Электронная услуга:</b>\n"
            if service.get("terms_online"):
                text += f"⏱️ <i>Срок:</i> {service.get('terms_online')}\n"
            if service.get("procedure_online"):
                text += f"📋 <i>Процедура:</i>\n{service.get('procedure_online')}\n"
        
        if service.get("documents"):
            text += f"📄 <i>Документы:</i> {service.get('documents')}\n"
    
    return text

def get_categories_keyboard(mode="current"):
    """Создание inline-клавиатуры с категориями"""
    categories = get_categories_list(mode)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, category in enumerate(categories):
        btn = InlineKeyboardButton(
            text=category["name"],
            callback_data=f"mfc_cat_{mode}_{i}"
        )
        keyboard.inline_keyboard.append([btn])
    
    # Если это меню текущих студентов - добавляем кнопку "Ранее обучавшимся"
    if mode == "current":
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="👥 Ранее обучавшимся", callback_data="mfc_old_services")
        ])
    
    # Кнопка возврата
    if mode == "old":
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 Вернуться к услугам МФЦ", callback_data="mfc_back_from_old")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")
    ])
    
    return keyboard

def get_services_keyboard(cat_index, mode="current"):
    """Создание inline-клавиатуры с услугами категории"""
    category = get_category_by_index(cat_index, mode)
    if not category:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К категориям", callback_data=f"mfc_back_to_categories_{mode}")],
            [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")],
        ])
    
    services = category.get("services", [])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for svc_idx, service in enumerate(services):
        btn = InlineKeyboardButton(
            text=service["name"],
            callback_data=f"mfc_service_{mode}_{cat_index}_{svc_idx}"
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 К категориям", callback_data=f"mfc_back_to_categories_{mode}")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")
    ])
    
    return keyboard

def get_service_detail_keyboard(cat_index, mode="current"):
    """Создание inline-клавиатуры для деталей услуги"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку услуг", callback_data=f"mfc_back_to_services_{mode}_{cat_index}")],
        [InlineKeyboardButton(text="🔙 К категориям", callback_data=f"mfc_back_to_categories_{mode}")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="mfc_back_to_menu")],
    ])

# ============= ОБРАБОТЧИКИ =============

@router.message(F.text == "📋 Услуги МФЦ")
async def handle_mfc_services(message: types.Message):
    """Начало работы с услугами МФЦ - показ категорий для текущих студентов"""
    if not mfc_services:
        await init_mfc_data()
    
    if not mfc_services:
        await send_or_edit_message(message, "❌ Услуги МФЦ временно недоступны")
        return
    
    text = "📋 <b>Услуги МФЦ</b>\n\n<i>Выбери статус и категорию услуг:</i>"
    keyboard = get_categories_keyboard("current")
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text == "📚 Студенту")
async def handle_student_menu(message: types.Message):
    """Обработчик для студентов - с кнопкой МФЦ"""
    student_text = "📚 <b>Информация для студентов</b>\n\nЗдесь ты найдешь всё что нужно для учёбы и жизни в университете.\n\nВыбери интересующий раздел:"
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
    await send_or_edit_message(message, student_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("mfc_cat_"))
async def handle_category_select(callback: types.CallbackQuery):
    """Обработчик выбора категории - показ услуг"""
    try:
        parts = callback.data.replace("mfc_cat_", "").split("_")
        mode = parts[0]
        cat_index = int(parts[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора категории", show_alert=True)
        return
    
    category = get_category_by_index(cat_index, mode)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"<b>{category['name']}</b>\n\n<i>Выбери услугу:</i>"
    keyboard = get_services_keyboard(cat_index, mode)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("mfc_service_"))
async def handle_service_select(callback: types.CallbackQuery):
    """Обработчик выбора услуги - показ деталей"""
    try:
        parts = callback.data.replace("mfc_service_", "").split("_")
        mode = parts[0]
        cat_index = int(parts[1])
        svc_index = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка выбора услуги", show_alert=True)
        return
    
    service = get_service_by_index(cat_index, svc_index, mode)
    if not service:
        await callback.answer("❌ Услуга не найдена", show_alert=True)
        return
    
    text = format_service_details(service)
    keyboard = get_service_detail_keyboard(cat_index, mode)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("mfc_back_to_categories_"))
async def handle_back_to_categories(callback: types.CallbackQuery):
    """Возврат к списку категорий"""
    try:
        mode = callback.data.replace("mfc_back_to_categories_", "")
    except (ValueError, IndexError):
        mode = "current"
    
    if not mfc_services and mode == "current":
        await init_mfc_data()
    
    if mode == "current":
        text = "📋 <b>Услуги МФЦ</b>\n\n<i>Выбери статус и категорию услуг:</i>"
    else:
        text = "👥 <b>Услуги для ранее обучавшихся</b>\n\n<i>Выбери категорию:</i>"
    
    keyboard = get_categories_keyboard(mode)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("mfc_back_to_services_"))
async def handle_back_to_services(callback: types.CallbackQuery):
    """Возврат к списку услуг категории"""
    try:
        parts = callback.data.replace("mfc_back_to_services_", "").split("_")
        mode = parts[0]
        cat_index = int(parts[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    category = get_category_by_index(cat_index, mode)
    if not category:
        await callback.answer("❌ Категория не найдена", show_alert=True)
        return
    
    text = f"<b>{category['name']}</b>\n\n<i>Выбери услугу:</i>"
    keyboard = get_services_keyboard(cat_index, mode)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "mfc_old_services")
async def handle_old_services(callback: types.CallbackQuery):
    """Переход к услугам для ранее обучавшихся"""
    if not mfc_old_services:
        await init_mfc_data()
    
    if not mfc_old_services:
        await callback.answer("❌ Услуги для ранее обучавшихся временно недоступны", show_alert=True)
        return
    
    text = "👥 <b>Услуги для ранее обучавшихся</b>\n\n<i>Выбери категорию:</i>"
    keyboard = get_categories_keyboard("old")
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "mfc_back_from_old")
async def handle_back_from_old(callback: types.CallbackQuery):
    """Возврат из услуг для ранее обучавшихся к текущим"""
    text = "📋 <b>Услуги МФЦ</b>\n\n<i>Выбери статус и категорию услуг:</i>"
    keyboard = get_categories_keyboard("current")
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "mfc_back_to_menu")
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

