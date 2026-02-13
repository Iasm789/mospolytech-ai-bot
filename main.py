"""
Основной файл приложения Telegram-бота МосПолитеха
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand

from config.settings import settings
from utils.logger import logger
from handlers.main_menu import router as main_menu_router
from handlers.schedule import router as schedule_router
from handlers.gigachat import router as gigachat_router



# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Подключение маршрутизаторов

dp.include_router(gigachat_router)  # GigaChat AI
dp.include_router(schedule_router)  # Расписание
dp.include_router(main_menu_router)


async def set_commands():
    """Установка команд бота"""
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="help", description="Справка"),
    ]
    await bot.set_my_commands(commands)


async def on_startup():
    """Инициализация при запуске бота"""
    logger.info("🚀 Бот запускается...")
    await set_commands()
    logger.info("✅ Бот успешно инициализирован")


async def on_shutdown():
    """Очистка при остановке бота"""
    logger.info("🛑 Бот останавливается...")
    await bot.session.close()


async def main():
    """Главная функция запуска бота"""
    try:
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        logger.info(f"Запуск поллинга... DEBUG режим: {settings.DEBUG}")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
