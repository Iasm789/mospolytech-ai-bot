"""
Обработчики главного меню и навигации
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from utils.logger import logger

router = Router()

# Клавиатура главного меню
def get_main_menu_keyboard():
    """Создание клавиатуры главного меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍🎓 Абитуриенту"), KeyboardButton(text="📚 Студенту")],
            [KeyboardButton(text="📰 Новости"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="💬 Обратная связь")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name or "Друг"
    
    welcome_text = (
        f"👋 Добро пожаловать, {user_name}!\n\n"
        "🎓 Я помощник Московского Политехнического Университета.\n\n"
        "Я помогу тебе:\n"
        "• 🎯 Выбрать направление обучения\n"
        "• 📅 Получить расписание занятий\n"
        "• 📋 Найти ответы на вопросы\n"
        "• 🔔 Получать уведомления о мероприятиях\n\n"
        "Выбери, что тебя интересует 👇"
    )
    
    logger.info(f"Новый пользователь: {user_name} (ID: {message.from_user.id})")
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Обработчик команды /menu"""
    await message.answer(
        "📌 Главное меню",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "❓ <b>Справка по использованию бота</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Запустить бота\n"
        "/menu - Показать меню\n"
        "/help - Эта справка\n\n"
        "<b>Функции для абитуриентов:</b>\n"
        "• Подбор направления по интересам\n"
        "• Расчёт баллов ЕГЭ\n"
        "• Проходные баллы прошлых лет\n"
        "• FAQ для поступающих\n\n"
        "<b>Функции для студентов:</b>\n"
        "• 📅 Расписание занятий для любой группы\n"
        "• Справочник преподавателей\n"
        "• Полезные ссылки\n\n"
        "💬 Если у тебя есть вопросы, используй меню 'Обратная связь'"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "👨‍🎓 Абитуриенту")
async def applicants_menu(message: types.Message):
    """Меню для абитуриентов"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Подбор направления")],
            [KeyboardButton(text="📊 Калькулятор ЕГЭ")],
            [KeyboardButton(text="📈 Проходные баллы")],
            [KeyboardButton(text="📅 Расписание ДОД")],
            [KeyboardButton(text="❓ FAQ абитуриента")],
            [KeyboardButton(text="◀️ Назад в меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await message.answer(
        "👨‍🎓 <b>Меню для абитуриентов</b>\n\n"
        "Выбери интересующий раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "📚 Студенту")
async def students_menu(message: types.Message):
    """Меню для студентов"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🤖 GigaChat AI")],
            [KeyboardButton(text="👨‍🏫 Преподаватели"), KeyboardButton(text="💡 База знаний")],
            [KeyboardButton(text="🔗 Полезные ссылки"), KeyboardButton(text="🔔 Напоминания")],
            [KeyboardButton(text="◀️ Назад в меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await message.answer(
        "📚 <b>Меню для студентов</b>\n\n"
        "Выбери интересующий раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "📰 Новости")
async def news_menu(message: types.Message):
    """Раздел новостей (заглушка)"""
    await message.answer(
        "📰 <b>Новости</b>\n\n"
        "Этот раздел ещё в разработке. "
        "Здесь будут самые свежие новости и объявления от университета. ⏳",
        parse_mode="HTML"
    )


@router.message(F.text == "❓ Помощь")
async def help_menu(message: types.Message):
    """Раздел помощи"""
    help_text = (
        "❓ <b>Как пользоваться ботом?</b>\n\n"
        "🎓 <b>Для абитуриентов:</b>\n"
        "В разделе 'Абитуриенту' ты найдёшь помощь при выборе направления, "
        "калькулятор для расчёта баллов и информацию о проходных баллах.\n\n"
        "📚 <b>Для студентов:</b>\n"
        "В разделе 'Студенту' доступны расписание, информация о преподавателях "
        "и полезные ссылки.\n\n"
        "💬 <b>Остались вопросы?</b>\n"
        "Воспользуйся 'Обратной связью' или напиши /help для подробной справки."
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "💬 Обратная связь")
async def feedback_menu(message: types.Message):
    """Раздел обратной связи"""
    await message.answer(
        "💬 <b>Обратная связь</b>\n\n"
        "Этот раздел ещё в разработке. "
        "Здесь ты сможешь задать анонимный вопрос администраторам. ⏳",
        parse_mode="HTML"
    )


@router.message(F.text == "◀️ Назад в меню")
async def back_to_menu(message: types.Message):
    """Возврат в главное меню"""
    await message.answer(
        "📌 Главное меню",
        reply_markup=get_main_menu_keyboard()
    )


# Обработчики для abiturent подразделов (заглушки)
@router.message(F.text == "🎯 Подбор направления")
async def speciality_guide(message: types.Message):
    await message.answer("🎯 Подбор направления обучения (в разработке)")


@router.message(F.text == "📊 Калькулятор ЕГЭ")
async def egz_calculator(message: types.Message):
    await message.answer("📊 Калькулятор ЕГЭ (в разработке)")


@router.message(F.text == "📈 Проходные баллы")
async def passing_scores(message: types.Message):
    await message.answer("📈 Проходные баллы (в разработке)")


@router.message(F.text == "📅 Расписание ДОД")
async def dod_schedule(message: types.Message):
    await message.answer("📅 Расписание дней открытых дверей (в разработке)")


@router.message(F.text == "❓ FAQ абитуриента")
async def faq_applicant(message: types.Message):
    await message.answer("❓ FAQ для абитуриентов (в разработке)")


# Обработчики для student подразделов
@router.message(F.text == "🤖 GigaChat AI")
async def gigachat_button(message: types.Message):
    """Переход к GigaChat AI"""
    await message.answer(
        "🤖 Жми /ask чтобы задать вопрос GigaChat AI или /gigachat_status для проверки подключения",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🤖 GigaChat AI")],
                [KeyboardButton(text="👨‍🏫 Преподаватели"), KeyboardButton(text="💡 База знаний")],
                [KeyboardButton(text="🔗 Полезные ссылки"), KeyboardButton(text="🔔 Напоминания")],
                [KeyboardButton(text="◀️ Назад в меню")],
            ],
            resize_keyboard=True
        )
    )


@router.message(F.text == "👨‍🏫 Преподаватели")
async def teachers(message: types.Message):
    await message.answer("👨‍🏫 Справочник преподавателей (в разработке)")


@router.message(F.text == "💡 База знаний")
async def knowledge_base(message: types.Message):
    await message.answer("💡 База знаний (в разработке)")


@router.message(F.text == "🔗 Полезные ссылки")
async def useful_links(message: types.Message):
    await message.answer("🔗 Полезные ссылки (в разработке)")


@router.message(F.text == "🔔 Напоминания")
async def reminders(message: types.Message):
    await message.answer("🔔 Управление напоминаниями (в разработке)")
