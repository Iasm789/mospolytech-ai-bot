"""
Обработчики для работы с GigaChat AI
"""

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from services.gigachat_service import gigachat_service
from utils.logger import logger

router = Router()


class GigaChatForm(StatesGroup):
    """Состояния для работы с GigaChat"""
    waiting_for_question = State()


@router.message(Command("ask"))
async def cmd_ask(message: types.Message, state: FSMContext):
    """Начать диалог с GigaChat через /ask"""
    
    if not gigachat_service.is_configured():
        await message.answer(
            "❌ GigaChat не настроен!\n\n"
            "Добавь в .env файл:\n"
            "• GIGACHAT_CLIENT_ID\n"
            "• GIGACHAT_CLIENT_SECRET\n\n"
            "Получить их можно на https://developers.sber.ru"
        )
        return
    
    await state.set_state(GigaChatForm.waiting_for_question)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Отмена")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🤖 Привет! Я GigaChat AI.\n\n"
        "Задай мне любой вопрос или напиши задачу:",
        reply_markup=keyboard
    )


@router.message(GigaChatForm.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext, bot: Bot):
    """Обработать вопрос пользователя"""
    
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="◀️ Назад")]],
            resize_keyboard=True
        ))
        return
    
    question = message.text
    
    # Показываем что печатаем
    await bot.send_chat_action(message.chat.id, "typing")
    
    logger.info(f"💬 Пользователь {message.from_user.id} спрашивает: {question}")
    
    # Отправляем запрос к GigaChat
    reply = gigachat_service.chat(question)
    
    if reply:
        # Разбиваем длинный ответ на части
        if len(reply) > 4090:
            parts = []
            current_part = ""
            
            for line in reply.split('\n'):
                if len(current_part) + len(line) + 1 > 4000:
                    parts.append(current_part)
                    current_part = line
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            for i, part in enumerate(parts):
                await message.answer(part)
                if i < len(parts) - 1:
                    await message.chat.typing()
        else:
            await message.answer(reply)
        
        logger.info(f"✅ Ответ отправлен пользователю {message.from_user.id}")
    else:
        await message.answer(
            "❌ Не удалось получить ответ от GigaChat.\n\n"
            "Возможные причины:\n"
            "• GigaChat API недоступен\n"
            "• Неверные credentails\n"
            "• Квота превышена\n\n"
            "Посмотри логи бота для деталей."
        )
        logger.error(f"❌ Ошибка при получении ответа для пользователя {message.from_user.id}")
    
    # Предлагаем ещё вопросы
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤖 Ещё вопрос")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True
    )
    
    await message.answer("Что дальше?", reply_markup=keyboard)
    
    await state.clear()


@router.message(F.text == "🤖 Ещё вопрос")
async def ask_again(message: types.Message, state: FSMContext):
    """Задать ещё один вопрос"""
    await state.set_state(GigaChatForm.waiting_for_question)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Отмена")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🤖 Слушаю! Задай следующий вопрос:",
        reply_markup=keyboard
    )


@router.message(Command("gigachat_status"))
async def cmd_status(message: types.Message):
    """Проверить статус GigaChat подключения"""
    
    if gigachat_service.is_configured():
        status_text = (
            "✅ <b>GigaChat настроен</b>\n\n"
            f"🔧 Client ID: {gigachat_service.client_id[:10]}...\n"
            f"🔑 Scope: {gigachat_service.scope}\n"
            f"🌐 API URL: {gigachat_service.api_url}\n"
        )
        
        # Пытаемся получить токен
        token = gigachat_service.get_token()
        if token:
            status_text += "✅ <b>Токен получен успешно!</b>\n"
            status_text += "🟢 <b>API готов к использованию</b>"
        else:
            status_text += "❌ <b>Не удалось получить токен</b>\n"
            status_text += "🔴 <b>Проверь credentials</b>"
    else:
        status_text = (
            "❌ <b>GigaChat не настроен</b>\n\n"
            "Добавь в .env файл:\n"
            "• GIGACHAT_CLIENT_ID\n"
            "• GIGACHAT_CLIENT_SECRET\n\n"
            "Инструкция: https://developers.sber.ru"
        )
    
    await message.answer(status_text, parse_mode="HTML")
    logger.info(f"📊 Пользователь {message.from_user.id} проверил статус GigaChat")
