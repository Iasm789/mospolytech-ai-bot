"""
Обработчики для раздела "Обратная связь"
"""

import uuid

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config.settings import settings
from handlers.navigation import BACK_TEXT, get_main_menu_keyboard
from models.feedback import Feedback
from services.feedback_service import get_feedback_service
from utils.logger import logger

router = Router()


class FeedbackForm(StatesGroup):
    """Состояния для формы обратной связи"""

    selecting_type = State()
    entering_title = State()
    entering_message = State()
    entering_rating = State()
    confirming = State()


def get_feedback_type_keyboard() -> ReplyKeyboardMarkup:
    """Получить клавиатуру выбора типа обратной связи"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Оставить отзыв")],
            [KeyboardButton(text="🐛 Сообщить об ошибке")],
            [KeyboardButton(text="💡 Предложить улучшение")],
            [KeyboardButton(text="📋 Другое")],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True,
    )


def get_rating_keyboard() -> ReplyKeyboardMarkup:
    """Получить клавиатуру оценок"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⭐ 1"),
                KeyboardButton(text="⭐⭐ 2"),
                KeyboardButton(text="⭐⭐⭐ 3"),
                KeyboardButton(text="⭐⭐⭐⭐ 4"),
                KeyboardButton(text="⭐⭐⭐⭐⭐ 5"),
            ],
            [KeyboardButton(text="Пропустить оценку")],
        ],
        resize_keyboard=True,
    )


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру подтверждения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="feedback_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="feedback_cancel"),
            ]
        ]
    )


@router.message(F.text == "💬 Обратная связь")
async def start_feedback(message: types.Message, state: FSMContext):
    """Начать процесс оставления обратной связи"""
    await state.set_state(FeedbackForm.selecting_type)

    feedback_intro = """
💬 ОБРАТНАЯ СВЯЗЬ

Спасибо за внимание к нашему боту! Твоё мнение очень важно для нас.

Выбери тип сообщения:
"""

    await message.answer(feedback_intro, reply_markup=get_feedback_type_keyboard())


@router.message(FeedbackForm.selecting_type)
async def handle_feedback_type(message: types.Message, state: FSMContext):
    """Обработать выбор типа обратной связи"""
    type_map = {
        "⭐ Оставить отзыв": "review",
        "🐛 Сообщить об ошибке": "bug_report",
        "💡 Предложить улучшение": "improvement",
        "📋 Другое": "other",
    }

    feedback_type = type_map.get(message.text)

    if not feedback_type:
        if message.text == BACK_TEXT:
            await state.clear()
            await message.answer(
                "Возвращаемся в главное меню", reply_markup=get_main_menu_keyboard()
            )
            return
        await message.answer("❌ Пожалуйста, выбери один из предложенных вариантов")
        return

    await state.update_data(feedback_type=feedback_type)

    # Если это баг-репорт или фича - просим заголовок
    if feedback_type in ["bug_report", "improvement"]:
        await state.set_state(FeedbackForm.entering_title)
        title_text = {
            "bug_report": "🐛 Опиши краткий заголовок ошибки:",
            "improvement": "💡 Опиши краткий заголовок предложения:",
        }
        await message.answer(
            title_text[feedback_type],
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Пропустить")], [KeyboardButton(text=BACK_TEXT)]],
                resize_keyboard=True,
            ),
        )
    else:
        # Для отзыва и других - идём сразу к сообщению
        await state.set_state(FeedbackForm.entering_message)
        message_text = {
            "review": "⭐ Напиши свой отзыв (поделись впечатлениями!):",
            "other": "📝 Напиши своё сообщение:",
        }
        await message.answer(
            message_text.get(feedback_type, "📝 Напиши своё сообщение:"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=BACK_TEXT)]], resize_keyboard=True
            ),
        )


@router.message(FeedbackForm.entering_title)
async def handle_feedback_title(message: types.Message, state: FSMContext):
    """Обработать заголовок"""
    if message.text == BACK_TEXT:
        await state.clear()
        await message.answer("Возвращаемся в главное меню", reply_markup=get_main_menu_keyboard())
        return

    title = None if message.text == "Пропустить" else message.text

    await state.update_data(title=title)
    await state.set_state(FeedbackForm.entering_message)

    await message.answer(
        "📝 Теперь напиши подробное описание:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True),
    )


@router.message(FeedbackForm.entering_message)
async def handle_feedback_message(message: types.Message, state: FSMContext):
    """Обработать основное сообщение"""
    if message.text == BACK_TEXT:
        await state.clear()
        await message.answer("Возвращаемся в главное меню", reply_markup=get_main_menu_keyboard())
        return

    if not message.text or len(message.text.strip()) < 5:
        await message.answer("❌ Пожалуйста, напиши сообщение не менее 5 символов")
        return

    await state.update_data(message=message.text)

    # Спросим оценку (если это отзыв)
    data = await state.get_data()
    if data.get("feedback_type") == "review":
        await state.set_state(FeedbackForm.entering_rating)
        await message.answer(
            "⭐ Оцени наш бот (от 1 до 5 звёзд):", reply_markup=get_rating_keyboard()
        )
    else:
        # Для других типов - сразу к подтверждению
        await show_confirmation(message, state)


@router.message(FeedbackForm.entering_rating)
async def handle_feedback_rating(message: types.Message, state: FSMContext):
    """Обработать оценку"""
    if message.text == BACK_TEXT:
        await state.clear()
        await message.answer("Возвращаемся в главное меню", reply_markup=get_main_menu_keyboard())
        return

    rating = None

    if message.text == "Пропустить оценку":
        rating = None
    elif message.text.startswith("⭐"):
        try:
            rating = int(message.text.count("⭐"))
            if rating not in [1, 2, 3, 4, 5]:
                await message.answer("❌ Пожалуйста, выбери оценку от 1 до 5 звёзд")
                return
        except ValueError:
            await message.answer("❌ Не удалось распознать оценку. Попробуй ещё раз")
            return
    else:
        await message.answer("❌ Пожалуйста, выбери оценку от 1 до 5 звёзд")
        return

    await state.update_data(rating=rating)

    # Переходим к подтверждению
    await show_confirmation(message, state)


async def show_confirmation(message: types.Message, state: FSMContext):
    """Показать подтверждение перед отправкой"""
    await state.set_state(FeedbackForm.confirming)
    data = await state.get_data()

    feedback_type_names = {
        "review": "⭐ Отзыв",
        "bug_report": "🐛 Баг-репорт",
        "improvement": "💡 Улучшение",
        "other": "📋 Другое",
    }

    feedback_type = feedback_type_names.get(data.get("feedback_type"), data.get("feedback_type"))
    title_line = ""
    if data.get("title"):
        title_line = f"📌 Заголовок: {data.get('title', '')[:50]}\n"
    rating_line = ""
    if data.get("rating"):
        rating_line = f"⭐ Оценка: {'★' * data.get('rating')}"

    confirmation_text = f"""
✅ ПОДТВЕРЖДЕНИЕ ОБРАТНОЙ СВЯЗИ

📋 Тип: {feedback_type}
{title_line}📝 Сообщение: {data.get('message', '')[:150]}...
{rating_line}

Всё верно? Отправить обратную связь?
"""

    await message.answer(confirmation_text, reply_markup=get_confirmation_keyboard())


@router.callback_query(FeedbackForm.confirming, F.data == "feedback_confirm")
async def confirm_feedback(query: types.CallbackQuery, state: FSMContext):
    """Подтвердить и сохранить обратную связь"""
    data = await state.get_data()

    try:
        # Создаём объект обратной связи
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            user_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            feedback_type=data.get("feedback_type", "other"),
            title=data.get("title"),
            message=data.get("message"),
            rating=data.get("rating"),
        )

        # Сохраняем в сервис
        service = get_feedback_service()
        success = service.add_feedback(feedback)

        if success:
            await query.answer("✅ Спасибо! Твоя обратная связь сохранена")
            await query.message.edit_text(
                "✅ Спасибо за твою обратную связь! 🙏\n\n"
                "Мы внимательно рассмотрим твои предложения и постараемся улучшить наш сервис.\n\n"
                "Если у тебя есть ещё комментарии - всегда рады их услышать! 😊",
                reply_markup=None,
            )
            logger.info(f"✅ Новая обратная связь от {query.from_user.id}: {feedback.feedback_id}")

            # Возвращаемся в главное меню
            await state.clear()
            await query.message.answer(
                "Возвращаемся в главное меню...", reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.answer("❌ Произошла ошибка при сохранении", show_alert=True)
            await query.message.edit_text("❌ Ошибка при сохранении обратной связи")
            await state.clear()

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении обратной связи: {e}")
        await query.answer("❌ Ошибка сервера", show_alert=True)
        await state.clear()


@router.callback_query(FeedbackForm.confirming, F.data == "feedback_cancel")
async def cancel_feedback(query: types.CallbackQuery, state: FSMContext):
    """Отменить ввод обратной связи"""
    await query.answer("Отмена")
    await query.message.edit_text("Возвращаемся в главное меню...", reply_markup=None)
    await state.clear()
    await query.message.answer("🏠 Главное меню", reply_markup=get_main_menu_keyboard())


# Команда для просмотра статистики по обратной связи (для администраторов)
@router.message(Command("feedback_stats"))
async def show_feedback_stats(message: types.Message):
    """Показать статистику обратной связи (только для админов)"""
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("⛔ Эта команда доступна только администраторам.")
        return

    service = get_feedback_service()
    stats = service.get_stats()

    stats_text = f"""
📊 СТАТИСТИКА ОБРАТНОЙ СВЯЗИ

Всего отзывов: {stats.total_count}
Средняя оценка: {'⭐' * (int(stats.average_rating) if stats.average_rating else 0)} {stats.average_rating}/5.0

По типам:
"""

    type_names = {
        "review": "⭐ Отзывы",
        "bug_report": "🐛 Баг-репорты",
        "feature_request": "💡 Предложения",
        "improvement": "📈 Улучшения",
        "other": "📋 Прочее",
    }

    for fb_type, count in stats.by_type.items():
        type_name = type_names.get(fb_type, fb_type)
        stats_text += f"\n  {type_name}: {count}"

    await message.answer(stats_text)
