"""
Обработчик для ответов на вопросы пользователей
Ищет ответы в FAQ JSON файле на основе ключевых слов
"""

import json
import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from config.settings import settings
from utils.logger import logger
from handlers.navigation import get_main_menu_keyboard
from services.local_ai_service import get_local_ai_service

router = Router()

# Путь к FAQ файлу
FAQ_DATA_PATH = Path(__file__).parent.parent / "docs" / "faq_questions.json"

# Кеш для FAQ данных
faq_data = None

# Синонимы и разговорные формы для более "человечного" поиска
SYNONYM_MAP = {
    "стипа": "стипендия",
    "стипу": "стипендия",
    "стипуха": "стипендия",
    "общага": "общежитие",
    "общагу": "общежитие",
    "общаге": "общежитие",
    "общагой": "общежитие",
    "общежитие": "общежитие",
    "расписон": "расписание",
    "пары": "расписание",
    "мфц": "многофункциональныйцентр",
    "льготы": "льгота",
}

TOPIC_KEYWORDS = {
    "dormitories": ("общежит", "общаг", "заселен", "проживан", "комнат"),
    "scholarships": ("стипенд", "выплат", "матпомощ", "социал"),
    "mfc": ("мфц", "справк", "документ", "заявлен", "услуг"),
    "schedule": ("расписан", "пары", "заняти", "групп"),
    "admission": ("абитур", "поступ", "факульт", "институт", "вуз"),
}

INTENT_KEYWORDS = {
    "admission": ("поступ", "абитур", "зачисл", "егэ", "проходн", "балл", "прием"),
    "dormitories": ("общежит", "заселен", "комнат", "прожив"),
    "scholarships": ("стипенд", "выплат", "матпомощ", "льгот"),
    "schedule": ("расписан", "пары", "заняти", "групп"),
    "mfc": ("мфц", "справк", "документ", "заявлен"),
    "events": ("мероприят", "конкурс", "культур", "волонтер"),
}


@dataclass(frozen=True)
class FaqCandidate:
    item: dict
    score: float
    coverage: float

OFFTOPIC_PATTERNS = (
    r"^\s*\d+\s*[\+\-\*/]\s*\d+\s*(?:=|\?)?\s*$",
    r"(погод|температур|дожд|снег|ветер)",
    r"(анекдот|мем|гороскоп|рецепт)",
    r"(курс доллара|биткоин|крипт|акции)",
)

EDU_MATH_CONTEXT_HINTS = (
    "егэ",
    "балл",
    "проходн",
    "конкурс",
    "бюджет",
    "договор",
    "поступ",
    "абитур",
    "прием",
    "направлен",
    "специальност",
)

DOMAIN_HINTS = (
    "мосполитех",
    "политех",
    "университет",
    "вуз",
    "студент",
    "абитуриент",
    "проект",
    "практик",
    "библиотек",
    "военно",
    "аспирант",
    "стип",
    "льгот",
    "мероприят",
    "кампус",
)

MEDICAL_ROOTS = (
    "мед",
    "омс",
    "полис",
    "врач",
    "терап",
    "клиник",
    "психолог",
    "здоров",
    "медпомощ",
)

FINANCIAL_AID_ROOTS = (
    "стип",
    "матпомощ",
    "профсоюз",
    "выплат",
    "льгот",
)

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


def normalize_text(text: str) -> str:
    """Приводит текст к каноничному виду для поиска."""
    lowered = text.lower().strip().replace("ё", "е")
    return re.sub(r"\s+", " ", lowered)


def tokenize(text: str) -> set[str]:
    """Разбивает текст на токены (слова/числа)."""
    normalized = normalize_text(text)
    return set(re.findall(r"[a-zа-я0-9]+", normalized))


def stem_ru_token(token: str) -> str:
    """
    Упрощенный стемминг русского слова без внешних библиотек.
    Нужен как fallback для близких словоформ.
    """
    suffixes = (
        "иями",
        "ями",
        "ами",
        "ией",
        "ией",
        "ией",
        "ого",
        "ему",
        "ому",
        "ах",
        "ях",
        "ов",
        "ев",
        "ей",
        "ой",
        "ий",
        "ый",
        "ая",
        "ое",
        "ые",
        "ие",
        "ия",
        "ью",
        "иям",
        "ям",
        "ам",
        "ом",
        "ем",
        "у",
        "ю",
        "а",
        "я",
        "ы",
        "и",
        "е",
        "о",
        "ь",
    )
    for suffix in suffixes:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def expand_tokens(tokens: set[str]) -> set[str]:
    """Расширяет набор токенов синонимами и стеммами."""
    expanded = set(tokens)
    for token in list(tokens):
        canonical = SYNONYM_MAP.get(token, token)
        expanded.add(canonical)
        expanded.add(stem_ru_token(canonical))
    return {token for token in expanded if token}


def detect_topic(text: str) -> str | None:
    """Определяет тему вопроса/FAQ по ключевым корням."""
    normalized = normalize_text(text)
    best_topic = None
    best_score = 0
    for topic, roots in TOPIC_KEYWORDS.items():
        score = sum(1 for root in roots if root in normalized)
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic if best_score > 0 else None


def is_domain_question(text: str) -> bool:
    """Проверяет, относится ли вопрос к домену бота (университет/студенческие сервисы)."""
    normalized = normalize_text(text)
    if detect_topic(normalized):
        return True
    return any(hint in normalized for hint in DOMAIN_HINTS)


def is_obvious_offtopic(text: str) -> bool:
    """Быстрый blacklist для очевидно нерелевантных запросов."""
    normalized = normalize_text(text)
    has_edu_math_context = any(hint in normalized for hint in EDU_MATH_CONTEXT_HINTS)
    if has_edu_math_context:
        return False
    return any(re.search(pattern, normalized) for pattern in OFFTOPIC_PATTERNS)


def classify_intent(text: str) -> tuple[str | None, float]:
    """Определить интент вопроса и confidence [0..1]."""
    normalized = normalize_text(text)
    scored: list[tuple[str, int]] = []
    for intent, roots in INTENT_KEYWORDS.items():
        score = sum(1 for root in roots if root in normalized)
        if score > 0:
            scored.append((intent, score))
    if not scored:
        return None, 0.0
    scored.sort(key=lambda item: item[1], reverse=True)
    best_intent, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0
    confidence = min(1.0, (best_score - second_score * 0.5) / max(best_score, 1))
    return best_intent, confidence


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


def _rank_faq_candidates(user_question: str, intent: str | None = None) -> list[FaqCandidate]:
    """Вернуть top FAQ кандидатов с учетом score и coverage."""
    if not faq_data or "faq" not in faq_data:
        return []

    normalized_question = normalize_text(user_question)
    question_tokens = expand_tokens(tokenize(normalized_question))
    question_coverage_tokens = {stem_ru_token(token) for token in tokenize(normalized_question)}
    question_topic = detect_topic(normalized_question)
    candidates: list[FaqCandidate] = []

    for faq_item in faq_data["faq"]:
        item_score = 0.0
        normalized_faq_question = normalize_text(faq_item.get("question", ""))
        keywords = faq_item.get("keywords", [])
        normalized_keywords = [normalize_text(keyword) for keyword in keywords]

        for keyword in normalized_keywords:
            if keyword and keyword in normalized_question:
                item_score += 2.0
            keyword_token_set = expand_tokens(tokenize(keyword))
            if question_tokens & keyword_token_set:
                item_score += 1.0

        keyword_tokens = set()
        for keyword in normalized_keywords:
            keyword_tokens.update(expand_tokens(tokenize(keyword)))

        keyword_coverage_tokens = {stem_ru_token(token) for token in tokenize(" ".join(normalized_keywords))}
        coverage = 0.0
        if question_coverage_tokens:
            coverage = len(question_coverage_tokens & keyword_coverage_tokens) / len(question_coverage_tokens)

        if question_tokens and keyword_tokens:
            overlap = len(question_tokens & keyword_tokens) / len(keyword_tokens)
            item_score += overlap * 2.0

        question_similarity = difflib.SequenceMatcher(
            None, normalized_question, normalized_faq_question
        ).ratio()
        item_score += question_similarity

        faq_question_tokens = expand_tokens(tokenize(normalized_faq_question))
        if question_tokens and faq_question_tokens:
            question_overlap = len(question_tokens & faq_question_tokens) / len(faq_question_tokens)
            item_score += question_overlap

        faq_topic_text = f"{normalized_faq_question} {' '.join(normalized_keywords)}"
        faq_topic = detect_topic(faq_topic_text)
        if question_topic and faq_topic and question_topic != faq_topic:
            item_score -= 1.2
        if intent and faq_topic and intent != faq_topic:
            item_score -= 0.8
        if intent and intent in normalized_faq_question:
            item_score += 0.4

        rerank_score = item_score + coverage * 1.5
        candidates.append(FaqCandidate(item=faq_item, score=rerank_score, coverage=coverage))

    candidates.sort(key=lambda item: (item.score, item.coverage), reverse=True)
    return candidates


def _is_faq_candidate_acceptable(candidates: list[FaqCandidate]) -> bool:
    if not candidates:
        return False
    top = candidates[0]
    if top.score < 0.9:
        return False
    return True


def is_faq_answer_covered(user_question: str, answer_item: dict) -> bool:
    """Проверка покрытия ответа ключевыми токенами вопроса."""
    question_tokens = {stem_ru_token(t) for t in tokenize(user_question)}
    answer_text = f"{answer_item.get('question', '')} {answer_item.get('answer', '')} {' '.join(answer_item.get('keywords', []))}"
    answer_tokens = {stem_ru_token(t) for t in tokenize(answer_text)}
    normalized_question = normalize_text(user_question)
    normalized_answer = normalize_text(answer_text)

    # Защита от частой коллизии: "медицинская помощь" и "материальная помощь".
    question_has_medical = any(root in normalized_question for root in MEDICAL_ROOTS)
    answer_has_medical = any(root in normalized_answer for root in MEDICAL_ROOTS)
    question_has_financial = any(root in normalized_question for root in FINANCIAL_AID_ROOTS)
    answer_has_financial = any(root in normalized_answer for root in FINANCIAL_AID_ROOTS)
    if question_has_medical and answer_has_financial and not answer_has_medical:
        return False
    if question_has_financial and answer_has_medical and not answer_has_financial:
        return False

    if not question_tokens:
        return False
    coverage = len(question_tokens & answer_tokens) / len(question_tokens)
    return coverage >= settings.LOCAL_AI_MIN_FAQ_COVERAGE


def find_answer(user_question: str, intent: str | None = None) -> dict | None:
    """
    Поиск ответа на вопрос пользователя
    
    Args:
        user_question: Вопрос пользователя
        
    Returns:
        Словарь с ответом или None если не найдено
    """
    if not faq_data or "faq" not in faq_data:
        logger.warning("⚠️ FAQ данные не загружены!")
        return None
    
    normalized_question = normalize_text(user_question)
    logger.info(f"🔎 Ищу ответ на: '{normalized_question}'")
    
    # Если вопрос пуст
    if not normalized_question or len(normalized_question) < 3:
        logger.warning(f"⚠️ Вопрос слишком короткий: {len(normalized_question)} символов")
        return None

    if not is_domain_question(normalized_question):
        logger.info("ℹ️ Вопрос не относится к домену бота, FAQ-пропуск")
        return None

    candidates = _rank_faq_candidates(normalized_question, intent=intent)
    if _is_faq_candidate_acceptable(candidates):
        best_item = candidates[0].item
        logger.info(
            f"✅ Найден лучший ответ: FAQ #{best_item.get('id')} (score={candidates[0].score:.2f})"
        )
        return best_item

    logger.warning(f"❌ Ответ не найден для вопроса: '{normalized_question[:50]}'")
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


async def send_answer_message(message: types.Message, response_text: str, parse_mode: str | None = None):
    """Единая отправка ответа пользователю с клавиатурой продолжения."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Еще вопрос?"), KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True,
    )
    if parse_mode:
        await message.answer(response_text, reply_markup=keyboard, parse_mode=parse_mode)
    else:
        await message.answer(response_text, reply_markup=keyboard)


async def send_offtopic_message(message: types.Message) -> None:
    """Вежливый ответ для вопросов вне домена бота."""
    response_text = (
        "Я помогаю по вопросам МосПолитеха: расписание, стипендии, общежития, "
        "услуги МФЦ, льготы и студенческие сервисы.\n\n"
        "Попробуй задать вопрос по этим темам или выбери раздел в меню ниже."
    )
    await message.answer(response_text, reply_markup=get_help_keyboard())


async def send_clarification_message(message: types.Message) -> None:
    """Уточнение при низкой уверенности интента."""
    response_text = (
        "Хочу ответить точнее, но пока не до конца понял тему вопроса.\n\n"
        "Уточни, пожалуйста, что именно интересует:\n"
        "• поступление и зачисление\n"
        "• общежития\n"
        "• стипендии и льготы\n"
        "• расписание\n"
        "• услуги МФЦ"
    )
    await message.answer(response_text, reply_markup=get_help_keyboard())


@router.message(F.text, ~F.text.in_(MENU_BUTTONS))
async def handle_user_question(message: types.Message, state: FSMContext):
    """
    Обработчик для вопросов пользователя
    
    Это ПОСЛЕДНИЙ обработчик, срабатывает для всех текстовых сообщений,
    которые:
    1. Не совпадают с другими фильтрами
    2. Не являются кнопками меню (исключены в MENU_BUTTONS)
    
    Работает во ВСЕХ состояниях для универсального ответа на вопросы
    """
    user_text = message.text.strip()
    logger.info(f"🤔 Пользователь {message.from_user.id} задал вопрос: '{user_text[:50]}'...")
    
    # Инициализируем FAQ если еще не было
    init_faq()

    try:
        ai_service = get_local_ai_service()
        answer_priority = settings.ANSWER_PRIORITY
        logger.info(f"⚙️ Приоритет ответов: {answer_priority}")

        if is_obvious_offtopic(user_text):
            logger.info("ℹ️ Обнаружен оффтоп по blacklist-паттернам")
            ai_service.note_quality_event("offtopic_blacklist", user_text, {})
            await send_offtopic_message(message)
            return

        intent, intent_confidence = classify_intent(user_text)
        should_send_clarification = intent_confidence < settings.LOCAL_INTENT_MIN_CONFIDENCE
        if intent_confidence < settings.LOCAL_INTENT_MIN_CONFIDENCE:
            logger.info("ℹ️ Низкая уверенность интента: %.2f", intent_confidence)
            ai_service.note_quality_event(
                "low_intent_confidence",
                user_text,
                {"intent": intent, "confidence": intent_confidence},
            )

        if answer_priority == "faq_first":
            answer_item = find_answer(user_text, intent=intent)
            if answer_item and is_faq_answer_covered(user_text, answer_item):
                response_text = f"🔍 *Найден ответ на твой вопрос:*\n\n"
                response_text += f"❓ *{answer_item['question']}*\n\n"
                response_text += f"{answer_item['answer']}"
                await send_answer_message(message, response_text, parse_mode="Markdown")
                logger.info(f"✅ Ответ из FAQ отправлен для вопроса: {user_text[:50]}")
                return

            logger.info("ℹ️ FAQ не нашел ответ, пробую Local AI...")
            ai_answer = await ai_service.answer_async(user_text)
            if ai_answer:
                await send_answer_message(message, ai_answer)
                logger.info(f"🤖 Local AI отправил ответ для вопроса: {user_text[:50]}")
                return
        else:
            logger.info("🔍 Ищу ответ через Local AI...")
            ai_answer = await ai_service.answer_async(user_text)
            if ai_answer:
                await send_answer_message(message, ai_answer)
                logger.info(f"🤖 Local AI отправил ответ для вопроса: {user_text[:50]}")
                return

            logger.info("ℹ️ Local AI не нашел ответ, пробую FAQ...")
            answer_item = find_answer(user_text, intent=intent)
            if answer_item and is_faq_answer_covered(user_text, answer_item):
                response_text = f"🔍 *Найден ответ на твой вопрос:*\n\n"
                response_text += f"❓ *{answer_item['question']}*\n\n"
                response_text += f"{answer_item['answer']}"
                await send_answer_message(message, response_text, parse_mode="Markdown")
                logger.info(f"✅ Ответ из FAQ отправлен для вопроса: {user_text[:50]}")
                return

        if should_send_clarification:
            await send_clarification_message(message)
            return

        if not is_domain_question(user_text):
            logger.info("ℹ️ Обнаружен оффтоп по доменной проверке")
            ai_service.note_quality_event("offtopic_domain", user_text, {})
            await send_offtopic_message(message)
            return

        ai_service.note_quality_event("no_answer", user_text, {"intent": intent})
        response_text = (
            "😔 К сожалению, я не нашел готовый ответ на твой вопрос.\n\n"
            "Попробуй:\n"
            "• Переформулировать вопрос\n"
            "• Использовать ключевые слова (например, \"расписание\", \"стипендия\", \"общежитие\")\n"
            "• Выбрать нужный раздел в меню ниже\n\n"
            "Если остались вопросы - обратись в нашу служу поддержки 📞"
        )
        await message.answer(response_text, reply_markup=get_help_keyboard(), parse_mode="Markdown")
        logger.info(f"❌ Local AI и FAQ не нашли ответ: {user_text[:50]}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке ответа: {e}")
        await message.answer("Я не смог понять твой вопрос. Попробуй переформулировать.", reply_markup=get_help_keyboard())


@router.message(F.text == "❓ Еще вопрос?")
async def handle_another_question(message: types.Message, state: FSMContext):
    """Обработчик для кнопки 'Еще вопрос?'"""
    logger.info(f"📌 Пользователь {message.from_user.id} хочет задать еще вопрос")
    await state.clear()
    response = (
        "Отлично! 😊 Задай свой следующий вопрос или выбери раздел в меню ниже.\n"
        "Я помогу находить ответы на вопросы о расписании, стипендиях, льготах и многом другом!"
    )
    
    await message.answer(response, reply_markup=get_main_menu_keyboard())
