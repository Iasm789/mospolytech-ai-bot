"""
Обработчик для ответов на вопросы пользователей
Ищет ответы в FAQ JSON файле на основе ключевых слов
"""

import json
import difflib
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from utils.logger import logger

router = Router()

# Путь к FAQ файлу
FAQ_DATA_PATH = Path(__file__).parent.parent / "docs" / "faq_questions.json"

# Кеш для FAQ данных
faq_data = None

# ==================== КНОПКИ МЕНЮ, ЧТО НЕ ДОЛЖНЫ ОБРАБАТЫВАТЬСЯ КАК ВОПРОСЫ ====================
# Это кнопки из navigation.py и других обработчиков
MENU_BUTTONS = {
    # Основное меню
    "👨‍🎓 Абитуриенту",
    "📚 Студенту", 
    "🎪 Мероприятия",
    "📞 Контакты",
    "❓ Помощь",
    "💬 Обратная связь",
    
    # Меню студента
    "📅 Расписание занятий",
    "📋 Услуги МФЦ",
    "💰 Стипендии",
    "🏘️ Общежития",
    "📚 Студенческие Проекты",
    "🎓 Аспирантура",
    "📗 Льготы студентов",
    "📖 Библиотека",
    "🎖️ Военнообязанным",
    
    # Подкатегории льгот
    "💰 Стипендия",
    "🤝 Материальная помощь",
    "🏛️ Материальная поддержка (Мэрия)",
    "🚇 Льготный проезд",
    "📋 Все льготы",
    "📝 Как оформить",
    
    # Категории мероприятий
    "🎓 Обучение",
    "💼 Карьера",
    "🏆 Конкурсы",
    "🎭 Культура",
    "🎉 Студенческая жизнь",
    "🤝 Волонтёрство",
    
    # Навигация
    "◀️ Назад",
    "◀️ Назад в главное меню",
    "🏠 Главное меню",
    "❓ Еще вопрос?",
    "📋 Все мероприятия",
    "🔍 Поиск мероприятия",
    
    # Другие кнопки
    "📰 Новости",
    "📂 Служба поддержки",
}


def load_faq_data():
    """Загрузка FAQ данных из JSON"""
    try:
        with open(FAQ_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ FAQ данные успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке FAQ: {e}")
        return None


def init_faq():
    """Инициализация FAQ при запуске"""
    global faq_data
    if faq_data is None:
        faq_data = load_faq_data()


def find_answer(user_question: str) -> dict | None:
    """
    Поиск ответа на вопрос пользователя
    
    Args:
        user_question: Вопрос пользователя
        
    Returns:
        Словарь с ответом или None если не найдено
    """
    if not faq_data or "faq" not in faq_data:
        return None
    
    user_question_lower = user_question.lower().strip()
    
    # Если вопрос пуст
    if not user_question_lower or len(user_question_lower) < 3:
        return None
    
    # Сначала ищем точное совпадение по ключевым словам
    matches = []
    
    for faq_item in faq_data["faq"]:
        keywords = faq_item.get("keywords", [])
        
        # Проверяем, содержится ли любое ключевое слово в вопросе
        for keyword in keywords:
            if keyword.lower() in user_question_lower:
                matches.append(faq_item)
                break
    
    # Если есть совпадения по ключевым словам, возвращаем первое
    if matches:
        return matches[0]
    
    # Если прямых совпадений нет, используем нечеткий поиск по вопросам
    questions = [faq["question"].lower() for faq in faq_data["faq"]]
    close_matches = difflib.get_close_matches(
        user_question_lower, 
        questions, 
        n=1, 
        cutoff=0.6
    )
    
    if close_matches:
        # Находим соответствующий FAQ элемент
        for faq_item in faq_data["faq"]:
            if faq_item["question"].lower() == close_matches[0]:
                return faq_item
    
    return None


def get_help_keyboard() -> ReplyKeyboardMarkup:
    """Получить клавиатуру с подсказками"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Студенту")],
            [KeyboardButton(text="👨‍🎓 Абитуриенту")],
            [KeyboardButton(text="📋 Служба поддержки")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )


@router.message(F.text, ~F.text.in_(MENU_BUTTONS), StateFilter(None))
async def handle_user_question(message: types.Message, state: FSMContext):
    """
    Обработчик для вопросов пользователя
    
    Это ПОСЛЕДНИЙ обработчик, срабатывает для всех текстовых сообщений,
    которые:
    1. Не совпадают с другими фильтрами
    2. Не являются кнопками меню (исключены в MENU_BUTTONS)
    3. Пользователь находится в начальном состоянии (не в процессе заполнения формы)
    """
    user_text = message.text.strip()
    
    # Инициализируем FAQ если еще не было
    init_faq()
    
    # Ищем ответ на вопрос
    answer_item = find_answer(user_text)
    
    if answer_item:
        # Найден ответ
        response_text = f"🔍 **Найден ответ на твой вопрос:**\n\n"
        response_text += f"❓ {answer_item['question']}\n\n"
        response_text += f"{answer_item['answer']}"
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="❓ Еще вопрос?"), KeyboardButton(text="🏠 Главное меню")],
            ],
            resize_keyboard=True
        )
        
        await message.answer(response_text, reply_markup=keyboard, parse_mode="HTML")
        logger.info(f"✅ Ответ найден для вопроса: {user_text[:50]}")
    else:
        # Ответ не найден
        response_text = (
            "😔 К сожалению, я не нашел готовый ответ на твой вопрос.\n\n"
            "Попробуй:\n"
            "• Переформулировать вопрос\n"
            "• Использовать ключевые слова (например, \"расписание\", \"стипендия\", \"общежитие\")\n"
            "• Выбрать нужный раздел в меню ниже\n\n"
            "Если остались вопросы - обратись в нашу служу поддержки 📞"
        )
        
        await message.answer(response_text, reply_markup=get_help_keyboard(), parse_mode="HTML")
        logger.info(f"❌ Ответ не найден для вопроса: {user_text[:50]}")
