"""
Обработчики для программ обучения и абитуриентов
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import math

from services.programs_service import programs_service
from utils.logger import logger

router = Router()
PROGRAMS_PER_PAGE = 6  # Количество программ на странице


class ProgramsForm(StatesGroup):
    """Состояния для просмотра программ"""
    selecting_faculty = State()
    viewing_faculty_programs = State()
    viewing_program_detail = State()
    searching = State()
    search_results = State()


def get_faculty_icons() -> dict:
    """Получение иконок для факультетов"""
    icons = {
        "fm": "🤖",  # Мехатроника
        "fit": "💻",  # Информационные технологии
        "fche": "🧪",  # Химия и биология
        "ft": "⚙️",  # Технология
        "f_ekonomiki": "💼",  # Экономика
        "f_iskusstva": "🎨",  # Искусство
        "f_izdatelskogo": "📖",  # Издательское дело
        "f_poligraficheskogo": "🖨️",  # Полиграфическое дело
        "f_urbanistiki": "🏙️",  # Урбанистика
        "other": "📚",  # Прочие
    }
    return icons


def get_programs_main_keyboard():
    """Клавиатура главного меню программ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Все факультеты", callback_data="programs_faculties")],
        [InlineKeyboardButton(text="🔍 Поиск программы", callback_data="programs_search")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main_menu_programs")],
    ])
    return keyboard


def get_faculties_keyboard(faculties: list, show_count: bool = True):
    """Создание инлайн клавиатуры с факультетами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    icons = get_faculty_icons()
    
    for idx, faculty in enumerate(faculties):
        icon = icons.get(faculty.id, "📚")
        count = len(programs_service.get_programs_by_faculty(faculty.id))
        count_text = f" ({count})" if show_count and count > 0 else ""
        
        button = InlineKeyboardButton(
            text=f"{icon} {faculty.name[:40]}{count_text}",
            callback_data=f"fac_{faculty.id}"
        )
        keyboard.inline_keyboard.append([button])
    
    # Кнопка назад
    back_button = InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_programs_main")
    keyboard.inline_keyboard.append([back_button])
    
    return keyboard


def get_faculty_programs_keyboard(faculty_id: str, page: int = 0):
    """Создание клавиатуры с программами факультета"""
    programs = programs_service.get_programs_by_faculty(faculty_id)
    total_pages = math.ceil(len(programs) / PROGRAMS_PER_PAGE) if programs else 1
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Пагинация программ
    start_idx = page * PROGRAMS_PER_PAGE
    end_idx = start_idx + PROGRAMS_PER_PAGE
    page_programs = programs[start_idx:end_idx]
    
    for program in page_programs:
        # Форматированная кнопка с кодом программы
        button_text = f"📖 {program.title[:42]}"
        if program.code and program.code != "00.00.00":
            button_text += f"\n   ({program.code})"
        
        button = InlineKeyboardButton(
            text=button_text,
            callback_data=f"prog_{program.id}"
        )
        keyboard.inline_keyboard.append([button])
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"fac_page_{faculty_id}_{page-1}"))
    
    page_text = f"{page + 1}/{total_pages}" if total_pages > 1 else ""
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page_text}", callback_data="noop"))
    
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"fac_page_{faculty_id}_{page+1}"))
    
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)
    
    # Кнопка назад к факультетам
    back_button = InlineKeyboardButton(text="◀️ К факультетам", callback_data="back_to_faculties")
    keyboard.inline_keyboard.append([back_button])
    
    return keyboard


def format_program_card(program) -> str:
    """Форматировать информацию о программе в красивое сообщение"""
    faculty_name = programs_service.get_faculty_name(program.faculty_id)
    
    # Строим красивую карточку с улучшенным форматированием
    sections = []
    
    # Заголовок
    sections.append(f"📚 <b>{program.title}</b>")
    
    # Основная информация
    info_lines = []
    info_lines.append(f"🏢 <b>Факультет:</b> {faculty_name}")
    info_lines.append(f"📝 <b>Код:</b> {program.code}")
    
    if program.duration:
        info_lines.append(f"⏱️️ <b>Длительность:</b> {program.duration}")
    
    info_lines.append(f"📅 <b>Форма обучения:</b> {program.form}")
    
    if program.level:
        info_lines.append(f"🎓 <b>Уровень:</b> {program.level}")
    
    sections.append("\n".join(info_lines))
    
    # Описание
    if program.description:
        sections.append(f"📋 <b>О программе:</b>\n{program.description}")
    
    # Цель программы
    if program.goal:
        sections.append(f"🎯 <b>Цель программы:</b>\n{program.goal}")
    
    # Профиль
    if program.profile:
        sections.append(f"👨‍💼 <b>Профиль подготовки:</b>\n{program.profile}")
    
    # Дисциплины ЕГЭ
    if program.disciplines and len(program.disciplines) > 0:
        disciplines_str = ", ".join(program.disciplines)
        sections.append(f"📚 <b>Основные дисциплины ЕГЭ:</b>\n{disciplines_str}")
    
    # Проходной балл
    if program.min_score:
        sections.append(f"📊 <b>Средний проходной балл:</b> {program.min_score}")
    
    # Карьерные перспективы
    if program.career_prospects:
        sections.append(f"💼 <b>Карьерные перспективы:</b>\n{program.career_prospects}")
    
    # Возможные профессии
    if program.professions and len(program.professions) > 0:
        professions_str = ", ".join(program.professions)
        sections.append(f"🏆 <b>Возможные профессии:</b>\n{professions_str}")
    
    # Разделитель и ссылка
    sections.append("" + "─" * 30)
    sections.append(f"🔗 <a href='{program.url}'>Больше информации на сайте МосПолитеха</a>")
    
    text = "\n\n".join(sections)
    return text.strip()


def get_program_detail_keyboard(program_id: str):
    """Клавиатура для страницы программы"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть на сайте", url=programs_service.get_program_by_id(program_id).url if programs_service.get_program_by_id(program_id) else "#")],
        [InlineKeyboardButton(text="◀️ К программам факультета", callback_data="back_to_faculty_programs")],
        [InlineKeyboardButton(text="◀️ К факультетам", callback_data="back_to_faculties")],
    ])
    return keyboard


# ============== Обработчики команд ==============

@router.message(F.text == "📚 Программы обучения")
async def handle_programs(message: types.Message, state: FSMContext):
    """Обработчик для раздела Программы обучения"""
    programs_text = """
🎓 <b>Программы обучения МосПолитеха</b>

МосПолитех предлагает более 30 программ бакалавриата по 10 факультетам:

• 💻 Информационные технологии
• 🤖 Машиностроение и мехатроника
• 🧪 Химия и биотехнология
• 🚚 Транспорт и логистика
• 💼 Экономика и управление
• 🎨 Графика и изобразительное искусство
• 📖 Издательское дело
• 🖨️ Полиграфия
• 🏗️ Архитектура и градостроительство
• ⚡ Передовая инженерная школа FDR

<b>Выбери факультет</b>, чтобы увидеть доступные программы:
"""
    
    await state.set_state(ProgramsForm.selecting_faculty)
    await message.answer(programs_text, reply_markup=get_programs_main_keyboard(), parse_mode="HTML")


# ============== Обработчики callback'ов ==============

@router.callback_query(F.data == "programs_faculties")
async def show_faculties(query: types.CallbackQuery, state: FSMContext):
    """Показать список факультетов"""
    faculties = programs_service.get_faculties()
    
    if not faculties:
        await query.answer("❌ Факультеты не загружены", show_alert=True)
        return
    
    text = """
🏢 <b>Факультеты МосПолитеха</b>

Выбери факультет, чтобы увидеть программы обучения:
"""
    
    await state.set_state(ProgramsForm.selecting_faculty)
    await query.message.edit_text(text, reply_markup=get_faculties_keyboard(faculties), parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data.startswith("fac_"))
async def show_faculty_programs(query: types.CallbackQuery, state: FSMContext):
    """Показать программы факультета"""
    try:
        # Обработка пагинации
        if query.data.startswith("fac_page_"):
            parts = query.data.split("_")
            faculty_id = parts[2]
            page = int(parts[3]) if len(parts) > 3 else 0
        else:
            faculty_id = query.data[4:]  # Убираем "fac_"
            page = 0
        
        programs = programs_service.get_programs_by_faculty(faculty_id)
        faculty = programs_service.get_faculty_by_id(faculty_id)
        
        if not programs:
            await query.answer(f"❌ Программ для факультета не найдено", show_alert=True)
            return
        
        text = f"""
🎓 <b>{faculty.name}</b>

Программ обучения: <b>{len(programs)}</b>

Выбери интересующую программу для получения подробной информации:
"""
        
        await state.set_state(ProgramsForm.viewing_faculty_programs)
        await state.update_data(current_faculty=faculty_id)
        
        await query.message.edit_text(text, reply_markup=get_faculty_programs_keyboard(faculty_id, page), parse_mode="HTML")
        await query.answer()
    
    except Exception as e:
        logger.error(f"Ошибка при показе программ факультета: {e}")
        await query.answer("❌ Ошибка при загрузке программ", show_alert=True)


@router.callback_query(F.data.startswith("prog_"))
async def show_program_detail(query: types.CallbackQuery, state: FSMContext):
    """Показать детали программы"""
    try:
        program_id = query.data[5:]  # Убираем "prog_"
        program = programs_service.get_program_by_id(program_id)
        
        if not program:
            await query.answer("❌ Программа не найдена", show_alert=True)
            return
        
        text = format_program_card(program)
        
        await state.set_state(ProgramsForm.viewing_program_detail)
        await query.message.edit_text(text, reply_markup=get_program_detail_keyboard(program_id), parse_mode="HTML")
        await query.answer()
    
    except Exception as e:
        logger.error(f"Ошибка при показе деталей программы: {e}")
        await query.answer("❌ Ошибка при загрузке программы", show_alert=True)


@router.callback_query(F.data == "programs_search")
async def start_search(query: types.CallbackQuery, state: FSMContext):
    """Начать поиск программы"""
    await state.set_state(ProgramsForm.searching)
    
    text = """
🔍 <b>Поиск программы</b>

Введи название программы или ключевое слово:
"""
    
    back_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_programs_main")]
    ])
    
    await query.message.edit_text(text, reply_markup=back_button, parse_mode="HTML")
    await query.answer()


@router.message(ProgramsForm.searching)
async def process_search(message: types.Message, state: FSMContext):
    """Обработить поиск программы"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Введи минимум 2 символа для поиска")
        return
    
    results = programs_service.search_programs(query)
    
    if not results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="programs_search")],
            [InlineKeyboardButton(text="◀️ К факультетам", callback_data="back_to_faculties")],
        ])
        
        await message.answer(
            f"❌ По запросу '<b>{query}</b>' программ не найдено",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Показываем результаты поиска
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for program in results[:10]:  # Максимум 10 результатов
        button = InlineKeyboardButton(
            text=f"📖 {program.title}",
            callback_data=f"prog_{program.id}"
        )
        keyboard.inline_keyboard.append([button])
    
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад к поиску", callback_data="back_to_programs_main")])
    
    text = f"""
🔍 <b>Результаты поиска</b>

Найдено программ: <b>{len(results)}</b>

Выбери программу для подробной информации:
"""
    
    await state.set_state(ProgramsForm.search_results)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "back_to_faculties")
async def back_to_faculties(query: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку факультетов"""
    faculties = programs_service.get_faculties()
    
    text = """
📚 <b>Факультеты МосПолитеха</b>

Выбери факультет, чтобы увидеть его программы обучения:
"""
    
    await state.set_state(ProgramsForm.selecting_faculty)
    await query.message.edit_text(text, reply_markup=get_faculties_keyboard(faculties), parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data == "back_to_faculty_programs")
async def back_to_faculty_programs(query: types.CallbackQuery, state: FSMContext):
    """Вернуться к программам факультета"""
    data = await state.get_data()
    faculty_id = data.get("current_faculty", "")
    
    if not faculty_id:
        await back_to_faculties(query, state)
        return
    
    programs = programs_service.get_programs_by_faculty(faculty_id)
    faculty = programs_service.get_faculty_by_id(faculty_id)
    
    text = f"""
🎓 <b>{faculty.name}</b>

Программ обучения: <b>{len(programs)}</b>

Выбери интересующую программу для получения подробной информации:
"""
    
    await state.set_state(ProgramsForm.viewing_faculty_programs)
    await query.message.edit_text(text, reply_markup=get_faculty_programs_keyboard(faculty_id, 0), parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data == "back_to_programs_main")
async def back_to_programs_main(query: types.CallbackQuery, state: FSMContext):
    """Вернуться к главному меню программ"""
    text = """
🎓 <b>Программы обучения МосПолитеха</b>

МосПолитех предлагает более 30 программ бакалавриата по 10 факультетам:

• 💻 Информационные технологии
• 🤖 Машиностроение и мехатроника
• 🧪 Химия и биотехнология
• 🚚 Транспорт и логистика
• 💼 Экономика и управление
• 🎨 Графика и изобразительное искусство
• 📖 Издательское дело
• 🖨️ Полиграфия
• 🏗️ Архитектура и градостроительство
• ⚡ Передовая инженерная школа FDR

<b>Выбери факультет</b>, чтобы увидеть доступные программы:
"""
    
    await state.set_state(ProgramsForm.selecting_faculty)
    await query.message.edit_text(text, reply_markup=get_programs_main_keyboard(), parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data == "back_to_main_menu_programs")
async def back_to_main_menu(query: types.CallbackQuery, state: FSMContext):
    """Вернуться в главное меню"""
    aspirant_text = """
👨‍🎓 Информация для абитуриентов

МосПолитех - ведущий технический университет России, принимает студентов на множество интересных направлений.

Выбери, что тебя интересует:
"""
    
    from handlers.navigation import get_aspirant_menu_keyboard
    
    keyboard = get_aspirant_menu_keyboard()
    keyboard.one_time_keyboard = True
    
    await state.clear()
    try:
        await query.message.delete()
    except Exception:
        pass
    
    await query.message.chat.send_message(aspirant_text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()


@router.callback_query(F.data == "noop")
async def noop(query: types.CallbackQuery):
    """Пустое действие"""
    await query.answer()
