"""
Обработчики для студенческих проектов
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import math

from services.projects_service import projects_service
from utils.logger import logger

router = Router()
PROJECTS_PER_PAGE = 5  # Количество проектов на странице


class ProjectsForm(StatesGroup):
    """Состояния для просмотра проектов"""
    viewing_menu = State()
    viewing_category = State()
    viewing_category_projects = State()
    viewing_project_detail = State()
    searching = State()
    search_results = State()


def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍🎓 Абитуриенту"), KeyboardButton(text="📚 Студенту")],
            [KeyboardButton(text="📰 Новости"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="💬 Обратная связь")],
        ],
        resize_keyboard=True
    )


def get_projects_menu_keyboard():
    """Клавиатура меню проектов (inline версия)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Все категории", callback_data="projects_categories")],
        [InlineKeyboardButton(text="🔍 Поиск проекта", callback_data="projects_search")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="projects_stats")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main_menu_projects")],
    ])
    return keyboard


def get_categories_icons() -> dict:
    """Получение иконок для тематик проектов"""
    icons = {
        "IT": "💻",
        "Дизайн": "🎨",
        "Мультимедиа": "📹",
        "Научные проекты": "🔬",
        "Проекты технологического лидерства": "🚀",
        "Соцтех": "👥",
        "Стратегические проекты вуза": "🏛️",
        "Технология": "⚙️",
        "Транспорт": "🚗",
        "Урбанистика": "🏙️",
        "Химбиотех": "🧬",
        "Другое": "📂",
    }
    return icons


def get_categories_keyboard(categories: list, show_count: bool = True):
    """Создание инлайн клавиатуры с категориями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    icons = get_categories_icons()
    
    for idx, category in enumerate(categories):
        icon = icons.get(category, "📂")
        count = len(projects_service.get_projects_by_category(category))
        count_text = f" ({count})" if show_count else ""
        
        button = InlineKeyboardButton(
            text=f"{icon} {category[:35]}{count_text}",
            callback_data=f"cat_{idx}"
        )
        keyboard.inline_keyboard.append([button])
    
    # Кнопка назад
    back_button = InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_projects_menu")
    keyboard.inline_keyboard.append([back_button])
    
    return keyboard


def get_category_nav_keyboard(projects: list, page: int, category_idx: int, total_categories: int):
    """Создание клавиатуры с навигацией между категориями и пагинацией"""
    total_pages = math.ceil(len(projects) / PROJECTS_PER_PAGE)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    start_idx = page * PROJECTS_PER_PAGE
    end_idx = start_idx + PROJECTS_PER_PAGE
    
    # Проекты на этой странице
    for idx, project in enumerate(projects[start_idx:end_idx], start=start_idx):
        button = InlineKeyboardButton(
            text=f"📌 {project.title[:32]}",
            callback_data=f"prj_{category_idx}_{idx}"
        )
        keyboard.inline_keyboard.append([button])
    
    # Навигация по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"pg_{category_idx}_{page - 1}"
        ))
    
    page_info = InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="page_info"
    )
    nav_buttons.append(page_info)
    
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"pg_{category_idx}_{page + 1}"
        ))
    
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)
    
    # Навигация между категориями
    cat_nav_buttons = []
    if category_idx > 0:
        cat_nav_buttons.append(InlineKeyboardButton(
            text="◀️ Пред. кат",
            callback_data=f"cat_nav_{category_idx - 1}"
        ))
    
    cat_nav_buttons.append(InlineKeyboardButton(
        text="📂 Категории",
        callback_data="back_to_categories"
    ))
    
    if category_idx + 1 < total_categories:
        cat_nav_buttons.append(InlineKeyboardButton(
            text="Сл. кат ➡️",
            callback_data=f"cat_nav_{category_idx + 1}"
        ))
    
    if cat_nav_buttons:
        keyboard.inline_keyboard.append(cat_nav_buttons)
    
    # Кнопка "Назад в меню"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_projects_menu")
    ])
    
    return keyboard


def get_projects_pagination_keyboard(projects: list, page: int, category_idx: int, total_categories: int = 0):
    """Создание клавиатуры с пагинацией для списка проектов (deprecated - используйте get_category_nav_keyboard)"""
    return get_category_nav_keyboard(projects, page, category_idx, total_categories or 5)


def get_project_detail_keyboard(project_id: str):
    """Создание клавиатуры для детального просмотра проекта"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть на сайте", url=f"https://projects.mospolytech.ru/")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_projects")],
    ])
    return keyboard


# Обработчик входа в раздел Студенческие Проекты
@router.message(F.text == "📚 Студенческие Проекты")
async def student_projects_menu(message: types.Message, state: FSMContext):
    """Главное меню студенческих проектов"""
    
    try:
        # Инициализируем проекты при первом входе
        if not projects_service.projects_data:
            success = await projects_service.init_projects()
            
            if not success:
                await message.answer(
                    "❌ Не удалось загрузить проекты. Попробуйте позже."
                )
                return
        
        await state.set_state(ProjectsForm.viewing_menu)
        
        summary = projects_service.get_projects_summary()
        
        welcome_text = (
            "🎓 <b>Студенческие Проекты</b>\n"
            f"Всего: {summary['total']}"
        )
        
        await message.answer(welcome_text, reply_markup=get_projects_menu_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в student_projects_menu: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


# Обработчик просмотра всех категорий (callback и message)
@router.callback_query(F.data == "projects_categories")
async def view_all_categories_callback(callback: types.CallbackQuery, state: FSMContext):
    """Просмотр всех категорий проектов (callback handler)"""
    await view_all_categories(callback, state)


@router.message(F.text == "📚 Все категории")
async def handle_all_categories_from_menu(message: types.Message, state: FSMContext):
    """Обработка нажатия на Все категории из разных меню"""
    await view_all_categories(message, state)


async def view_all_categories(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    """Просмотр всех категорий проектов"""
    
    if not projects_service.projects_data:
        text = "❌ Проекты не загружены. Пожалуйста, перезагрузитесь в меню проектов."
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer(text, reply_markup=get_projects_menu_keyboard())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=get_projects_menu_keyboard())
            await message_or_callback.answer()
        return
    
    categories = projects_service.get_all_categories()
    
    if not categories:
        text = "❌ Категории не найдены."
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer(text, reply_markup=get_projects_menu_keyboard())
        else:
            await message_or_callback.message.edit_text(text, reply_markup=get_projects_menu_keyboard())
            await message_or_callback.answer()
        return
    
    await state.set_state(ProjectsForm.viewing_category)
    
    text = "📂 <b>Выберите категорию</b>"
    
    keyboard = get_categories_keyboard(categories, show_count=True)
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await message_or_callback.answer()


# Обработчик выбора категории
@router.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    
    try:
        cat_idx = int(callback.data.replace("cat_", ""))
        categories = projects_service.get_all_categories()
        
        if cat_idx >= len(categories):
            await callback.answer("❌ Категория не найдена.", show_alert=True)
            return
        
        category = categories[cat_idx]
        projects = projects_service.get_projects_by_category(category)
        
        if not projects:
            await callback.answer(f"ℹ️ В категории '{category}' пока нет проектов.", show_alert=True)
            return
        
        await state.set_state(ProjectsForm.viewing_category_projects)
        await state.update_data(
            current_category=category,
            current_category_idx=cat_idx,
            current_page=0,
            projects=projects
        )
        
        # Показываем первую страницу проектов
        await show_category_projects(callback, category, projects, 0, cat_idx)
    except Exception as e:
        logger.error(f"Ошибка в category_selected: {e}")
        await callback.answer("❌ Ошибка при выборе категории.", show_alert=True)


# Обработчик навигации между категориями
@router.callback_query(F.data.startswith("cat_nav_"))
async def navigate_category(callback: types.CallbackQuery, state: FSMContext):
    """Обработка навигации между категориями (< >)"""
    
    try:
        cat_idx = int(callback.data.replace("cat_nav_", ""))
        categories = projects_service.get_all_categories()
        
        if cat_idx < 0 or cat_idx >= len(categories):
            await callback.answer("❌ Категория не найдена.", show_alert=True)
            return
        
        category = categories[cat_idx]
        projects = projects_service.get_projects_by_category(category)
        
        if not projects:
            await callback.answer(f"ℹ️ В категории '{category}' пока нет проектов.", show_alert=True)
            return
        
        await state.update_data(
            current_category=category,
            current_category_idx=cat_idx,
            current_page=0,
            projects=projects
        )
        
        await show_category_projects(callback, category, projects, 0, cat_idx)
    except Exception as e:
        logger.error(f"Ошибка в navigate_category: {e}")
        await callback.answer("❌ Ошибка при переходе между категориями.", show_alert=True)


async def show_category_projects(callback: types.CallbackQuery, category: str, projects: list, page: int, category_idx: int):
    """Показать проекты категории с пагинацией"""
    
    categories = projects_service.get_all_categories()
    total_categories = len(categories)
    total_pages = math.ceil(len(projects) / PROJECTS_PER_PAGE) if projects else 1
    start_idx = page * PROJECTS_PER_PAGE
    end_idx = start_idx + PROJECTS_PER_PAGE
    
    icons = get_categories_icons()
    icon = icons.get(category, "📂")
    
    text = f"{icon} <b>{category}</b>\n"
    text += f"Страница <b>{page + 1}/{total_pages}</b> | Всего: <b>{len(projects)}</b> проектов\n\n"
    
    if projects[start_idx:end_idx]:
        for idx, project in enumerate(projects[start_idx:end_idx], start=start_idx + 1):
            text += f"{idx}. <b>{project.title[:50]}</b>\n"
            if project.goal:
                text += f"    🎯 {project.goal[:70]}...\n"
            text += "\n"
    else:
        text += "❌ В этой категории пока нет проектов."
    
    keyboard = get_category_nav_keyboard(projects, page, category_idx, total_categories)
    
    if callback.message:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.answer(text, show_alert=True)
    
    await callback.answer()


# Обработчик пагинации
@router.callback_query(F.data.startswith("pg_"))
async def handle_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Обработка пагинации"""
    
    try:
        data = await state.get_data()
        callback_data = callback.data.replace("pg_", "")
        
        parts = callback_data.split("_")
        cat_idx = int(parts[0])
        page = int(parts[1])
        
        # Получаем категорию по индексу
        categories = projects_service.get_all_categories()
        if cat_idx >= len(categories):
            await callback.answer("❌ Категория не найдена.", show_alert=True)
            return
        
        category = categories[cat_idx]
        projects = projects_service.get_projects_by_category(category)
        
        if not projects:
            await callback.answer("❌ Проекты не найдены.", show_alert=True)
            return
        
        total_pages = math.ceil(len(projects) / PROJECTS_PER_PAGE)
        
        # Проверка границ страницы
        if page < 0 or page >= total_pages:
            await callback.answer(f"❌ Страница {page + 1} не существует.", show_alert=True)
            return
        
        await state.update_data(current_page=page, projects=projects)
        await show_category_projects(callback, category, projects, page, cat_idx)
    except ValueError:
        logger.error(f"Ошибка парсинга в handle_pagination: {callback.data}")
        await callback.answer("❌ Ошибка при обработке запроса.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в handle_pagination: {e}")
        await callback.answer("❌ Ошибка при переходе на страницу.", show_alert=True)


# Обработчик информации о странице (когда нажимают на номер страницы)
@router.callback_query(F.data == "page_info")
async def handle_page_info(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на информацию о странице"""
    
    try:
        data = await state.get_data()
        current_page = data.get("current_page", 0)
        current_category = data.get("current_category", "Неизвестная категория")
        projects = data.get("projects", [])
        
        total_pages = math.ceil(len(projects) / PROJECTS_PER_PAGE) if projects else 1
        
        info_text = (
            f"📄 <b>Информация о странице</b>\n\n"
            f"📂 Категория: <i>{current_category}</i>\n"
            f"📍 Текущая страница: <b>{current_page + 1}</b> из <b>{total_pages}</b>\n"
            f"📊 Всего проектов: <b>{len(projects)}</b>\n"
            f"📝 На странице: <b>{min(PROJECTS_PER_PAGE, len(projects) - current_page * PROJECTS_PER_PAGE)}</b>"
        )
        
        await callback.answer(info_text, show_alert=False)
    except Exception as e:
        logger.error(f"Ошибка в handle_page_info: {e}")
        await callback.answer("ℹ️ Не удалось получить информацию.", show_alert=False)


# Обработчик просмотра деталей проекта
@router.callback_query(F.data.startswith("prj_"))
async def view_project_detail(callback: types.CallbackQuery, state: FSMContext):
    """Просмотр детальной информации о проекте"""
    
    try:
        data = await state.get_data()
        callback_data = callback.data.replace("prj_", "")
        
        parts = callback_data.split("_")
        cat_idx = int(parts[0])
        proj_idx = int(parts[1])
        
        # Получаем категорию
        categories = projects_service.get_all_categories()
        if cat_idx >= len(categories):
            await callback.answer("❌ Категория не найдена.", show_alert=True)
            return
        
        category = categories[cat_idx]
        projects = projects_service.get_projects_by_category(category)
        
        if proj_idx >= len(projects):
            await callback.answer("❌ Проект не найден.", show_alert=True)
            return
        
        project = projects[proj_idx]
        
        await state.set_state(ProjectsForm.viewing_project_detail)
        await state.update_data(
            viewing_project_idx=proj_idx, 
            viewing_category_idx=cat_idx,
            viewing_from="category"
        )
        
        text = projects_service.format_project_detailed(project)
        keyboard = get_project_detail_keyboard(project.id)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except ValueError:
        logger.error(f"Ошибка парсинга в view_project_detail: {callback.data}")
        await callback.answer("❌ Ошибка при открытии проекта.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в view_project_detail: {e}")
        await callback.answer("❌ Ошибка при открытии проекта.", show_alert=True)


# Обработчик поиска проектов (text и callback)
@router.message(F.text == "🔍 Поиск проекта")
async def search_projects_message(message: types.Message, state: FSMContext):
    """Начало поиска проектов (message handler)"""
    await search_projects(message, state)


@router.callback_query(F.data == "projects_search")
async def search_projects_callback(callback: types.CallbackQuery, state: FSMContext):
    """Начало поиска проектов (callback handler)"""
    await search_projects(callback, state)


async def search_projects(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    """Начало поиска проектов"""
    
    categories = projects_service.get_all_categories()
    
    # Создаем клавиатуру с категориями для быстрого фильтра
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    icons = get_categories_icons()
    for idx, category in enumerate(categories):
        icon = icons.get(category, "📂")
        button = InlineKeyboardButton(
            text=f"{icon} {category[:35]}",
            callback_data=f"search_cat_{idx}"
        )
        keyboard.inline_keyboard.append([button])
    
    # Добавляем кнопку для общего поиска
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔍 Поиск везде", callback_data="search_all")
    ])
    
    # Кнопка отмены
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_projects_menu")
    ])
    
    text = (
        "🔍 <b>Поиск проекта</b>\n\n"
        "Выберите категорию для поиска или ищите везде:"
    )
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await message_or_callback.answer()
    
    await state.set_state(ProjectsForm.searching)


# Обработчик выбора категории для поиска
@router.callback_query(F.data.startswith("search_cat_"))
async def search_in_category(callback: types.CallbackQuery, state: FSMContext):
    """Выбор категории для поиска"""
    
    try:
        cat_idx = int(callback.data.replace("search_cat_", ""))
        categories = projects_service.get_all_categories()
        
        if cat_idx >= len(categories):
            await callback.answer("❌ Категория не найдена.", show_alert=True)
            return
        
        category = categories[cat_idx]
        
        await state.update_data(search_category=category, search_all_categories=False)
        await callback.message.edit_text(
            f"🔍 Введите ключевое слово для поиска в категории:\n"
            f"<b>{category}</b>\n\n"
            f"Или нажмите /отмена",
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в search_in_category: {e}")
        await callback.answer("❌ Ошибка при выборе категории.", show_alert=True)


# Обработчик поиска везде
@router.callback_query(F.data == "search_all")
async def search_everywhere(callback: types.CallbackQuery, state: FSMContext):
    """Выбор поиска по всем категориям"""
    
    await state.update_data(search_all_categories=True)
    await callback.message.edit_text(
        "🔍 Введите ключевое слово для поиска по всем проектам:\n\n"
        "Или нажмите /отмена",
        parse_mode="HTML"
    )
    await callback.answer()


# Обработчик текста при поиске
@router.message(ProjectsForm.searching)
async def handle_search(message: types.Message, state: FSMContext):
    """Обработка поиска"""
    
    if message.text.lower() in ["/отмена", "отмена"]:
        await state.set_state(ProjectsForm.viewing_menu)
        await message.answer(
            "🚪 Возвращаемся в меню проектов...",
            reply_markup=get_projects_menu_keyboard()
        )
        return
    
    query = message.text
    data = await state.get_data()
    search_all_categories = data.get("search_all_categories", True)
    search_category = data.get("search_category", None)
    
    # Поиск по категории или везде
    if search_all_categories or not search_category:
        results = projects_service.search_projects(query)
    else:
        # Ищем только в выбранной категории
        all_results = projects_service.search_projects(query)
        results = [p for p in all_results if p.category == search_category]
    
    if not results:
        await message.answer(
            f"❌ По запросу '{query}' ничего не найдено.",
            reply_markup=get_projects_menu_keyboard()
        )
        await state.set_state(ProjectsForm.viewing_menu)
        return
    
    await state.set_state(ProjectsForm.search_results)
    await state.update_data(search_results=results, search_query=query, current_page=0)
    
    text = f"🔍 <b>Результаты поиска по '{query}'</b>\n"
    text += f"Найдено: <b>{len(results)}</b> проектов\n\n"
    
    # Показываем первые результаты
    for i, project in enumerate(results[:PROJECTS_PER_PAGE], 1):
        text += f"{i}. <b>{project.title[:40]}</b>\n"
        text += f"   📂 {project.category}\n\n"
    
    # Создаем клавиатуру для результатов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for idx, project in enumerate(results[:PROJECTS_PER_PAGE]):
        button = InlineKeyboardButton(
            text=f"📌 {project.title[:35]}",
            callback_data=f"srch_{idx}"
        )
        keyboard.inline_keyboard.append([button])
    
    # Навигация
    if len(results) > PROJECTS_PER_PAGE:
        nav_buttons = []
        nav_buttons.append(InlineKeyboardButton(text="Далее ➡️", callback_data="search_next"))
        keyboard.inline_keyboard.append(nav_buttons)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 К меню", callback_data="back_to_projects_menu")
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")





# Обработчик переходa на следующую страницу поиска
@router.callback_query(F.data == "search_next")
async def search_next_page(callback: types.CallbackQuery, state: FSMContext):
    """Переход на следующую страницу результатов поиска"""
    
    try:
        data = await state.get_data()
        search_results = data.get("search_results", [])
        current_page = data.get("current_page", 0)
        search_query = data.get("search_query", "")
        
        current_page += 1
        total_pages = math.ceil(len(search_results) / PROJECTS_PER_PAGE)
        
        if current_page >= total_pages:
            await callback.answer("❌ Больше результатов нет.", show_alert=True)
            return
        
        start_idx = current_page * PROJECTS_PER_PAGE
        end_idx = start_idx + PROJECTS_PER_PAGE
        
        text = f"🔍 <b>Результаты поиска по '{search_query}'</b>\n"
        text += f"Страница <b>{current_page + 1}/{total_pages}</b>\n\n"
        
        for i, project in enumerate(search_results[start_idx:end_idx], 1):
            text += f"{i}. <b>{project.title[:40]}</b>\n"
            text += f"   📂 {project.category}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for idx, project in enumerate(search_results[start_idx:end_idx], start=start_idx):
            button = InlineKeyboardButton(
                text=f"📌 {project.title[:35]}",
                callback_data=f"srch_{idx}"
            )
            keyboard.inline_keyboard.append([button])
        
        # Навигация
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Пред",
                callback_data="search_prev"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}",
            callback_data="page_info"
        ))
        
        if current_page + 1 < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="Далее ➡️",
                callback_data="search_next"
            ))
        
        if nav_buttons:
            keyboard.inline_keyboard.append(nav_buttons)
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🏠 К меню", callback_data="back_to_projects_menu")
        ])
        
        await state.update_data(current_page=current_page)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в search_next_page: {e}")
        await callback.answer("❌ Ошибка при переходе на страницу.", show_alert=True)


# Обработчик возврата на предыдущую страницу поиска
@router.callback_query(F.data == "search_prev")
async def search_prev_page(callback: types.CallbackQuery, state: FSMContext):
    """Возврат на предыдущую страницу результатов поиска"""
    
    try:
        data = await state.get_data()
        search_results = data.get("search_results", [])
        current_page = data.get("current_page", 1)
        search_query = data.get("search_query", "")
        
        current_page -= 1
        
        if current_page < 0:
            await callback.answer("❌ Это первая страница.", show_alert=True)
            return
        
        total_pages = math.ceil(len(search_results) / PROJECTS_PER_PAGE)
        start_idx = current_page * PROJECTS_PER_PAGE
        end_idx = start_idx + PROJECTS_PER_PAGE
        
        text = f"🔍 <b>Результаты поиска по '{search_query}'</b>\n"
        text += f"Страница <b>{current_page + 1}/{total_pages}</b>\n\n"
        
        for i, project in enumerate(search_results[start_idx:end_idx], 1):
            text += f"{i}. <b>{project.title[:40]}</b>\n"
            text += f"   📂 {project.category}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for idx, project in enumerate(search_results[start_idx:end_idx], start=start_idx):
            button = InlineKeyboardButton(
                text=f"📌 {project.title[:35]}",
                callback_data=f"srch_{idx}"
            )
            keyboard.inline_keyboard.append([button])
        
        # Навигация
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Пред",
                callback_data="search_prev"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}",
            callback_data="page_info"
        ))
        
        if current_page + 1 < total_pages:
            nav_buttons.append(InlineKeyboardButton(
                text="Далее ➡️",
                callback_data="search_next"
            ))
        
        if nav_buttons:
            keyboard.inline_keyboard.append(nav_buttons)
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🏠 К меню", callback_data="back_to_projects_menu")
        ])
        
        await state.update_data(current_page=current_page)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в search_prev_page: {e}")
        await callback.answer("❌ Ошибка при переходе на страницу.", show_alert=True)








# Обработчик статистики проектов (text и callback)
@router.message(F.text == "📊 Статистика проектов")
async def view_statistics_message(message: types.Message, state: FSMContext):
    """Просмотр статистики проектов (message handler)"""
    await view_statistics(message, state)


@router.callback_query(F.data == "projects_stats")
async def view_statistics_callback(callback: types.CallbackQuery, state: FSMContext):
    """Просмотр статистики проектов (callback handler)"""
    await view_statistics(callback, state)


async def view_statistics(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    """Просмотр статистики проектов"""
    
    summary = projects_service.get_projects_summary()
    icons = get_categories_icons()
    
    text = "📊 <b>Статистика проектов</b>\n\n"
    text += f"<b>Всего проектов:</b> <b>{summary['total']}</b>\n\n"
    text += "<b>Распределение по категориям:</b>\n\n"
    
    for category, count in sorted(summary['by_category'].items()):
        percentage = (count / summary['total'] * 100) if summary['total'] > 0 else 0
        icon = icons.get(category, "📂")
        # Создаём визуальный прогресс-бар
        bar_length = 10
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        text += f"{icon} {category}\n"
        text += f"   {bar} {count} ({percentage:.1f}%)\n\n"
    
    if summary['last_updated']:
        text += f"📅 <i>Последнее обновление: {summary['last_updated'].strftime('%d.%m.%Y %H:%M')}</i>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 К меню проектов", callback_data="back_to_projects_menu")],
    ])
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await message_or_callback.answer()
    
    await state.set_state(ProjectsForm.viewing_menu)


# Обработчик обновления данных
@router.message(F.text == "🔄 Обновить данные")
async def refresh_data(message: types.Message, state: FSMContext):
    """Обновление данных проектов"""
    
    await message.answer("⏳ Обновление данных проектов... Это может занять несколько минут.")
    
    success = await projects_service.init_projects(force_refresh=True)
    
    if success:
        summary = projects_service.get_projects_summary()
        await message.answer(
            f"✅ Данные обновлены!\n\n"
            f"📊 Всего проектов: <b>{summary['total']}</b>",
            reply_markup=get_projects_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Не удалось обновить данные. Попробуйте позже.",
            reply_markup=get_projects_menu_keyboard()
        )
    
    await state.set_state(ProjectsForm.viewing_menu)


# Обработчик кнопок назад
@router.callback_query(F.data == "back_to_projects_menu")
async def back_to_projects_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в меню проектов"""
    
    await state.set_state(ProjectsForm.viewing_menu)
    
    summary = projects_service.get_projects_summary()
    
    text = f"🎓 Студенческие Проекты (Всего: {summary['total']})"
    
    await callback.message.edit_text(text, reply_markup=get_projects_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery, state: FSMContext):
    """Возврат к списку категорий"""
    
    categories = projects_service.get_all_categories()
    
    icons = get_categories_icons()
    text = "📂 <b>Все категории проектов:</b>\n\n"
    for category in categories:
        icon = icons.get(category, "📂")
        count = len(projects_service.get_projects_by_category(category))
        text += f"{icon} <b>{category}</b>\n"
        text += f"   📊 <i>Проектов: {count}</i>\n\n"
    
    keyboard = get_categories_keyboard(categories, show_count=True)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    await state.set_state(ProjectsForm.viewing_category)


@router.callback_query(F.data.startswith("srch_"))
async def view_search_project(callback: types.CallbackQuery, state: FSMContext):
    """Просмотр проекта из результатов поиска"""
    
    try:
        data = await state.get_data()
        search_results = data.get("search_results", [])
        
        proj_idx = int(callback.data.replace("srch_", ""))
        
        if proj_idx >= len(search_results):
            await callback.answer("❌ Проект не найден.", show_alert=True)
            return
        
        project = search_results[proj_idx]
        
        await state.set_state(ProjectsForm.viewing_project_detail)
        await state.update_data(viewing_search_idx=proj_idx, viewing_from="search")
        
        text = projects_service.format_project_detailed(project)
        keyboard = get_project_detail_keyboard(project.id)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except ValueError:
        logger.error(f"Ошибка парсинга в view_search_project: {callback.data}")
        await callback.answer("❌ Ошибка при открытии проекта.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в view_search_project: {e}")
        await callback.answer("❌ Ошибка при открытии проекта.", show_alert=True)





# Кнопка для возврата в детальном просмотре
@router.callback_query(F.data == "back_to_projects")
async def back_to_projects(callback: types.CallbackQuery, state: FSMContext):
    """Возврат из детального просмотра"""
    
    data = await state.get_data()
    viewing_from = data.get("viewing_from", "category")
    
    if viewing_from == "search":
        # Возвращаемся к результатам поиска
        search_results = data.get("search_results", [])
        search_query = data.get("search_query", "")
        current_page = data.get("current_page", 0)
        
        total_pages = math.ceil(len(search_results) / PROJECTS_PER_PAGE)
        start_idx = current_page * PROJECTS_PER_PAGE
        end_idx = start_idx + PROJECTS_PER_PAGE
        
        text = f"🔍 <b>Результаты поиска по '{search_query}'</b>\n"
        text += f"Страница <b>{current_page + 1}/{total_pages}</b>\n\n"
        
        for i, project in enumerate(search_results[start_idx:end_idx], 1):
            text += f"{i}. <b>{project.title[:40]}</b>\n"
            text += f"   📂 {project.category}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for idx, project in enumerate(search_results[start_idx:end_idx], start=start_idx):
            button = InlineKeyboardButton(
                text=f"📌 {project.title[:35]}",
                callback_data=f"srch_{idx}"
            )
            keyboard.inline_keyboard.append([button])
        
        # Навигация
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Пред", callback_data="search_prev"))
        
        nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="page_info"))
        
        if current_page + 1 < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Далее ➡️", callback_data="search_next"))
        
        if nav_buttons:
            keyboard.inline_keyboard.append(nav_buttons)
        
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🏠 К меню", callback_data="back_to_projects_menu")])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(ProjectsForm.search_results)
    
    else:  # category
        category = data.get("current_category", "")
        page = data.get("current_page", 0)
        category_idx = data.get("current_category_idx", 0)
        
        if category:
            projects = projects_service.get_projects_by_category(category)
            await show_category_projects(callback, category, projects, page, category_idx)
            await state.set_state(ProjectsForm.viewing_category_projects)
        else:
            await back_to_projects_menu(callback, state)
    
    await callback.answer()


# Обработчик возврата в главное меню (message и callback)
@router.message(F.text == "➡️ Назад в меню")
async def back_to_main_menu_message(message: types.Message, state: FSMContext):
    """Возврат в главное меню (message handler)"""
    await back_to_main_menu(message, state)


@router.callback_query(F.data == "back_to_main_menu_projects")
async def back_to_main_menu_projects_callback(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в меню проектов (callback handler)"""
    await back_to_projects_menu(callback, state)


async def back_to_main_menu(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    
    await state.clear()
    
    text = "🏠 Возвращаемся в главное меню."
    
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=get_main_menu_keyboard())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
        await message_or_callback.answer()

