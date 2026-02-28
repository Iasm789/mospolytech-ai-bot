"""
Обработчики для раздела "Мероприятия" с красивым форматированием и пагинацией
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from utils.logger import logger
from utils.message_manager import send_or_edit_message, reset_last_message_id
from services.events_service import get_events_service
from handlers.navigation import get_events_menu_keyboard, get_main_menu_keyboard

router = Router()

# Размер страницы для пагинации
EVENTS_PER_PAGE = 3
SEARCH_RESULTS_PER_PAGE = 5


class EventSearchState(StatesGroup):
    """Состояния для поиска мероприятий"""
    waiting_for_search = State()


def create_events_keyboard(events: list, category: str, page: int = 0):
    """Создать inline-клавиатуру для событий с пагинацией"""
    total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Добавляем кнопки для каждого события на этой странице
    start_idx = page * EVENTS_PER_PAGE
    end_idx = min(start_idx + EVENTS_PER_PAGE, len(events))
    
    for idx in range(start_idx, end_idx):
        event = events[idx]
        event_id = event.get('id', '')
        title = event.get('title', 'Без названия')[:30] + "..."
        
        callback_data = f"event:{event_id}:{category}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"📌 {title}", callback_data=callback_data)
        ])
    
    # Кнопки пагинации
    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{category}:{page-1}")
        )
    
    pagination_row.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"page:{category}:{page+1}")
        )
    
    if pagination_row:
        keyboard.inline_keyboard.append(pagination_row)
    
    # Кнопка "В меню"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="� Главное меню", callback_data="back_to_events_menu")
    ])
    
    return keyboard


@router.message(F.text == "🎪 Мероприятия")
async def handle_events(message: types.Message):
    """Обработчик раздела мероприятий"""
    events_text = """
🎪 <b>Мероприятия МосПолитеха</b>

Выбери категорию мероприятий, которая тебя интересует:
"""
    
    await send_or_edit_message(message, events_text, reply_markup=get_events_menu_keyboard(), parse_mode="HTML")


async def show_all_events(message: types.Message, page: int = 0):
    """Показать все события со всех категорий с пагинацией"""
    service = get_events_service()
    all_events_dict = await service.get_all_events()
    
    # Объединяем все события со всеми категориями
    all_events = []
    for category, events_list in all_events_dict.items():
        for event in events_list:
            all_events.append({**event, 'category': category})
    
    if not all_events:
        await send_or_edit_message(message, 
            f"❌ Мероприятия не найдены.",
            reply_markup=get_events_menu_keyboard()
        )
        return
    
    # Определяем диапазон для этой страницы
    total_pages = (len(all_events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
    if page >= total_pages:
        page = total_pages - 1
    
    start_idx = page * EVENTS_PER_PAGE
    end_idx = min(start_idx + EVENTS_PER_PAGE, len(all_events))
    
    # Заголовок
    text = f"<b>📋 Все мероприятия МосПолитеха</b>\n"
    text += f"📊 Страница {page + 1}/{total_pages} (всего: {len(all_events)})\n\n"
    
    # Показываем события на этой странице
    for idx in range(start_idx, end_idx):
        event = all_events[idx]
        time_str = event.get('time', 'Время не указано')
        place = event.get('place', 'Место не указано')
        title = event.get('title', 'Без названия')
        category = event.get('category', 'unknown')
        
        # Очищаем заголовок
        title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
        
        text += f"<b>{title}</b>\n"
        text += f"⏰ {time_str}\n"
        text += f"📍 {place}\n"
        text += "─────────────────────\n\n"
    
    text += f"<i>Нажми на название события, чтобы увидеть полную информацию</i>"
    
    # Создаем клавиатуру для всех событий
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Добавляем кнопки для каждого события на этой странице
    for idx in range(start_idx, end_idx):
        event = all_events[idx]
        event_id = event.get('id', '')
        title = event.get('title', 'Без названия')[:30] + "..."
        category = event.get('category', 'unknown')
        
        callback_data = f"event:{event_id}:{category}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"📌 {title}", callback_data=callback_data)
        ])
    
    # Кнопки пагинации
    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"all_page:{page-1}")
        )
    
    pagination_row.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"all_page:{page+1}")
        )
    
    if pagination_row:
        keyboard.inline_keyboard.append(pagination_row)
    
    # Кнопка "В меню"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🎪 В меню", callback_data="back_to_events_menu")
    ])
    
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "📋 Все мероприятия")
async def handle_all_events(message: types.Message):
    """Обработчик всех мероприятий"""
    await show_all_events(message, 0)


async def show_category_events(message: types.Message, category: str, category_name: str, page: int = 0):
    """Показать события категории с пагинацией"""
    service = get_events_service()
    events = await service.get_events_by_category(category)
    
    if not events:
        await send_or_edit_message(message, 
            f"❌ Мероприятия в категории '{category_name}' не найдены.",
            reply_markup=get_events_menu_keyboard()
        )
        return
    
    # Определяем диапазон для этой страницы
    total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
    if page >= total_pages:
        page = total_pages - 1
    
    start_idx = page * EVENTS_PER_PAGE
    end_idx = min(start_idx + EVENTS_PER_PAGE, len(events))
    
    # Заголовок
    text = f"<b>{category_name} - Мероприятия</b>\n"
    text += f"📊 Страница {page + 1}/{total_pages} (всего: {len(events)})\n\n"
    
    # Показываем события на этой странице
    for idx in range(start_idx, end_idx):
        event = events[idx]
        time_str = event.get('time', 'Время не указано')
        place = event.get('place', 'Место не указано')
        title = event.get('title', 'Без названия')
        
        # Очищаем заголовок
        title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
        
        text += f"<b>{title}</b>\n"
        text += f"⏰ {time_str}\n"
        text += f"📍 {place}\n"
        text += "─────────────────────\n\n"
    
    text += f"<i>Нажми на название события, чтобы увидеть полную информацию</i>"
    
    keyboard = create_events_keyboard(events, category, page)
    
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "🎓 Обучение")
async def handle_education_events(message: types.Message):
    """Мероприятия по обучению"""
    await show_category_events(message, "education", "🎓 Обучение")


@router.message(F.text == "💼 Карьера")
async def handle_careers_events(message: types.Message):
    """Мероприятия по карьере"""
    await show_category_events(message, "careers", "💼 Карьера")


@router.message(F.text == "🏆 Конкурсы")
async def handle_competitions_events(message: types.Message):
    """Мероприятия - конкурсы"""
    await show_category_events(message, "competitions", "🏆 Конкурсы")


@router.message(F.text == "🎭 Культура")
async def handle_culture_events(message: types.Message):
    """Мероприятия по культуре"""
    await show_category_events(message, "culture", "🎭 Культура")


@router.message(F.text == "🎉 Студенческая жизнь")
async def handle_student_life_events(message: types.Message):
    """Мероприятия студенческой жизни"""
    await show_category_events(message, "student_life", "🎉 Студенческая жизнь")


@router.message(F.text == "🤝 Волонтёрство")
async def handle_volunteering_events(message: types.Message):
    """Мероприятия волонтёрства"""
    await show_category_events(message, "volunteering", "🤝 Волонтёрство")


@router.message(F.text == "🔍 Поиск мероприятия")
async def start_search(message: types.Message, state: FSMContext):
    """Начать поиск мероприятия"""
    await state.set_state(EventSearchState.waiting_for_search)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Отмена")],
        ],
        resize_keyboard=True
    )
    
    await send_or_edit_message(message, 
        "🔍 <b>Поиск мероприятия</b>\n\nВведи название или ключевые слова для поиска:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(EventSearchState.waiting_for_search, F.text != "◀️ Отмена")
async def search_events(message: types.Message, state: FSMContext):
    """Поиск мероприятий"""
    query = message.text.strip()
    service = get_events_service()
    
    results = await service.search_events(query)
    
    if not results:
        await send_or_edit_message(message, 
            f"❌ Мероприятия с запросом <b>'{query}'</b> не найдены.",
            reply_markup=get_events_menu_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Показываем первую страницу результатов
    total_results = len(results)
    page = 0
    total_pages = (total_results + SEARCH_RESULTS_PER_PAGE - 1) // SEARCH_RESULTS_PER_PAGE
    
    start_idx = page * SEARCH_RESULTS_PER_PAGE
    end_idx = min(start_idx + SEARCH_RESULTS_PER_PAGE, total_results)
    
    text = f"🔍 <b>Результаты поиска</b>\n"
    text += f"<i>Найдено: {total_results} мероприятий</i>\n"
    text += f"📊 Страница {page + 1}/{total_pages}\n\n"
    
    # Создаём клавиатуру для результатов поиска
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for idx in range(start_idx, end_idx):
        event, category = results[idx]
        event_id = event.get('id', '')
        title = event.get('title', 'Без названия')[:35] + "..."
        
        callback_data = f"event:{event_id}:{category}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"📌 {title}", callback_data=callback_data)
        ])
        
        # Показываем краткую информацию
        text += f"<b>{event.get('title', 'Без названия')}</b>\n"
        text += f"⏰ {event.get('time', 'Время не указано')}\n"
        text += f"📍 {event.get('place', 'Место не указано')}\n"
        text += "─────────────────────\n\n"
    
    # Добавляем кнопки пагинации
    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"search_page:{query}:{page-1}")
        )
    
    pagination_row.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"search_page:{query}:{page+1}")
        )
    
    if pagination_row:
        keyboard.inline_keyboard.append(pagination_row)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="� Главное меню", callback_data="back_to_events_menu")
    ])
    
    await send_or_edit_message(message, text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()


@router.message(EventSearchState.waiting_for_search, F.text == "◀️ Отмена")
async def cancel_search(message: types.Message, state: FSMContext):
    """Отменить поиск"""
    await state.clear()
    await send_or_edit_message(message, 
        "❌ Поиск отменён.",
        reply_markup=get_events_menu_keyboard()
    )


# ============== Callback обработчики ==============

@router.callback_query(F.data == "noop")
async def noop_callback(query: types.CallbackQuery):
    """Обработчик для кнопок, которые ничего не делают"""
    await query.answer("ℹ️ Это индикатор страницы")


@router.callback_query(F.data.startswith("event:"))
async def show_event_details(query: types.CallbackQuery):
    """Показать полную информацию о событии"""
    try:
        parts = query.data.split(":")
        if len(parts) < 3:
            await query.answer("❌ Ошибка данных")
            return
        
        event_id = parts[1]
        category = parts[2]
        
        service = get_events_service()
        events = await service.get_events_by_category(category)
        
        # Ищем событие по ID
        event = None
        for evt in events:
            if evt.get('id') == event_id:
                event = evt
                break
        
        if not event:
            await query.answer("❌ Событие не найдено")
            return
        
        # Форматируем полную информацию
        full_text = service.format_event_full(event, category)
        
        # Создаём клавиатуру для события
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        # Кнопка на Telegram, если есть ссылка
        telegram_url = event.get('telegram_url', '')
        if telegram_url:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="🔗 Перейти в Telegram", url=telegram_url)
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_category:{category}")
        ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🎪 В меню", callback_data="back_to_events_menu")
        ])
        
        # Пытаемся отредактировать основное сообщение
        try:
            await query.message.edit_text(full_text, reply_markup=keyboard, parse_mode="HTML")
        except TelegramBadRequest:
            # Если сообщение не изменилось, просто отправляем новое
            await query.message.edit_text(full_text, reply_markup=keyboard, parse_mode="HTML")
        
        await query.answer("✅ Информация о событии загружена")
        
    except Exception as e:
        logger.error(f"Ошибка при показе деталей события: {e}")
        await query.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("page:"))
async def handle_page_navigation(query: types.CallbackQuery):
    """Обработчик навигации по страницам"""
    try:
        parts = query.data.split(":")
        category = parts[1]
        page = int(parts[2])
        
        service = get_events_service()
        events = await service.get_events_by_category(category)
        
        if not events:
            await query.answer("❌ События не найдены")
            return
        
        # Определяем количество страниц
        total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0
        
        # Формируем страницу
        start_idx = page * EVENTS_PER_PAGE
        end_idx = min(start_idx + EVENTS_PER_PAGE, len(events))
        
        text = f"<b>{service.get_category_name(category)}</b>\n"
        text += f"📊 Страница {page + 1}/{total_pages} (всего: {len(events)})\n\n"
        
        for idx in range(start_idx, end_idx):
            event = events[idx]
            time_str = event.get('time', 'Время не указано')
            place = event.get('place', 'Место не указано')
            title = event.get('title', 'Без названия')
            
            # Очищаем заголовок
            title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
            
            text += f"<b>{title}</b>\n"
            text += f"⏰ {time_str}\n"
            text += f"📍 {place}\n"
            text += "─────────────────────\n\n"
        
        keyboard = create_events_keyboard(events, category, page)
        
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при навигации по страницам: {e}")
        await query.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("all_page:"))
async def handle_all_page_navigation(query: types.CallbackQuery):
    """Обработчик навигации по страницам всех мероприятий"""
    try:
        parts = query.data.split(":")
        page = int(parts[1])
        
        service = get_events_service()
        all_events_dict = await service.get_all_events()
        
        # Объединяем все события со всеми категориями
        all_events = []
        for category, events_list in all_events_dict.items():
            for event in events_list:
                all_events.append({**event, 'category': category})
        
        if not all_events:
            await query.answer("❌ События не найдены")
            return
        
        # Определяем количество страниц
        total_pages = (len(all_events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0
        
        # Формируем страницу
        start_idx = page * EVENTS_PER_PAGE
        end_idx = min(start_idx + EVENTS_PER_PAGE, len(all_events))
        
        text = f"<b>📋 Все мероприятия МосПолитеха</b>\n"
        text += f"📊 Страница {page + 1}/{total_pages} (всего: {len(all_events)})\n\n"
        
        for idx in range(start_idx, end_idx):
            event = all_events[idx]
            time_str = event.get('time', 'Время не указано')
            place = event.get('place', 'Место не указано')
            title = event.get('title', 'Без названия')
            
            # Очищаем заголовок
            title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
            
            text += f"<b>{title}</b>\n"
            text += f"⏰ {time_str}\n"
            text += f"📍 {place}\n"
            text += "─────────────────────\n\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        # Добавляем кнопки для каждого события на этой странице
        for idx in range(start_idx, end_idx):
            event = all_events[idx]
            event_id = event.get('id', '')
            title = event.get('title', 'Без названия')[:30] + "..."
            category = event.get('category', 'unknown')
            
            callback_data = f"event:{event_id}:{category}"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📌 {title}", callback_data=callback_data)
            ])
        
        # Кнопки пагинации
        pagination_row = []
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"all_page:{page-1}")
            )
        
        pagination_row.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"all_page:{page+1}")
            )
        
        if pagination_row:
            keyboard.inline_keyboard.append(pagination_row)
        
        # Кнопка "В меню"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🎪 В меню", callback_data="back_to_events_menu")
        ])
        
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при навигации по страницам всех мероприятий: {e}")
        await query.answer("❌ Произошла ошибка")


async def handle_search_page_navigation(query: types.CallbackQuery, state: FSMContext):
    """Обработчик навигации по страницам результатов поиска"""
    try:
        parts = query.data.split(":", 2)
        if len(parts) < 3:
            await query.answer("❌ Ошибка данных")
            return
        
        search_query = parts[1]
        page = int(parts[2])
        
        service = get_events_service()
        results = await service.search_events(search_query)
        
        if not results:
            await query.answer("❌ Результаты не найдены")
            return
        
        # Определяем количество страниц
        total_results = len(results)
        total_pages = (total_results + SEARCH_RESULTS_PER_PAGE - 1) // SEARCH_RESULTS_PER_PAGE
        if page >= total_pages:
            page = total_pages - 1
        if page < 0:
            page = 0
        
        # Формируем страницу
        start_idx = page * SEARCH_RESULTS_PER_PAGE
        end_idx = min(start_idx + SEARCH_RESULTS_PER_PAGE, total_results)
        
        text = f"🔍 <b>Результаты поиска</b>\n"
        text += f"<i>'{search_query}'</i>\n"
        text += f"📊 Страница {page + 1}/{total_pages}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for idx in range(start_idx, end_idx):
            event, category = results[idx]
            event_id = event.get('id', '')
            title = event.get('title', 'Без названия')[:35] + "..."
            
            callback_data = f"event:{event_id}:{category}"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📌 {title}", callback_data=callback_data)
            ])
            
            text += f"<b>{event.get('title', 'Без названия')}</b>\n"
            text += f"⏰ {event.get('time', 'Время не указано')}\n"
            text += f"📍 {event.get('place', 'Место не указано')}\n"
            text += "─────────────────────\n\n"
        
        # Добавляем кнопки пагинации
        pagination_row = []
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"search_page:{search_query}:{page-1}")
            )
        
        pagination_row.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"search_page:{search_query}:{page+1}")
            )
        
        if pagination_row:
            keyboard.inline_keyboard.append(pagination_row)
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🎪 Главное меню", callback_data="back_to_events_menu")
        ])
        
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при навигации по страницам поиска: {e}")
        await query.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("search_page:"))
async def search_page_navigation(query: types.CallbackQuery, state: FSMContext):
    """Обработчик навигации по страницам результатов поиска"""
    await handle_search_page_navigation(query, state)


@router.callback_query(F.data == "back_to_events_menu")
async def back_to_events_menu(query: types.CallbackQuery):
    """Вернуться в главное меню"""
    from handlers.main_menu import get_main_menu_keyboard
    text = "📋 <b>Главное меню</b>"
    
    # Удаляем старое сообщение и отправляем новое с обычной клавиатурой
    try:
        await query.message.delete()
    except Exception:
        pass
    
    # Отправляем новое сообщение (edit_text не поддерживает ReplyKeyboardMarkup)
    await query.message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data.startswith("back_to_category:"))
async def back_to_category(query: types.CallbackQuery):
    """Вернуться к списку событий категории"""
    try:
        category = query.data.split(":")[1]
        
        service = get_events_service()
        events = await service.get_events_by_category(category)
        
        if not events:
            await query.answer("❌ События не найдены")
            return
        
        category_names = {
            "education": "🎓 Обучение",
            "careers": "💼 Карьера",
            "competitions": "🏆 Конкурсы",
            "exhibitions": "🖼 Выставки",
            "culture": "🎭 Культура",
            "volunteering": "🤝 Волонтёрство",
            "student_life": "🎉 Студенческая жизнь"
        }
        
        # Показываем первую страницу
        page = 0
        total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
        
        start_idx = page * EVENTS_PER_PAGE
        end_idx = min(start_idx + EVENTS_PER_PAGE, len(events))
        
        text = f"<b>{category_names.get(category, category)}</b>\n"
        text += f"📊 Страница {page + 1}/{total_pages} (всего: {len(events)})\n\n"
        
        for idx in range(start_idx, end_idx):
            event = events[idx]
            time_str = event.get('time', 'Время не указано')
            place = event.get('place', 'Место не указано')
            title = event.get('title', 'Без названия')
            
            # Очищаем заголовок
            title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
            
            text += f"<b>{title}</b>\n"
            text += f"⏰ {time_str}\n"
            text += f"📍 {place}\n"
            text += "─────────────────────\n\n"
        
        keyboard = create_events_keyboard(events, category, page)
        
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при возврате к категории: {e}")
        await query.answer("❌ Произошла ошибка")


@router.message(F.text == "◀️ Назад")
async def back_to_main_menu_from_events(message: types.Message):
    """Вернуться в главное меню из раздела мероприятий"""
    await send_or_edit_message(message, "📋 <b>Главное меню</b>", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")



@router.message(F.text == "◀️ Назад")
async def back_to_main_menu_from_events(message: types.Message):
    """Вернуться в главное меню из раздела мероприятий"""
    await send_or_edit_message(message, "📋 Главное меню", reply_markup=get_main_menu_keyboard())


