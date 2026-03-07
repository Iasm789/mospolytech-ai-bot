"""
Основной файл приложения Telegram-бота МосПолитеха
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand

from config.settings import settings, validate_settings
from core.error_handler import setup_error_handlers
from utils.logger import logger
from utils.security import rate_limiter, session_manager
from services.events_service import init_events_service
from services.programs_service import init_programs_data
from handlers.main_menu import router as main_menu_router
from handlers.schedule import router as schedule_router
from handlers.mfc_services import router as mfc_services_router, init_mfc_data
from handlers.scholarships import router as scholarships_router, init_scholarships_data
from handlers.dormitories import router as dormitories_router, init_dormitories_data
from handlers.projects import router as projects_router
from handlers.events import router as events_router
from handlers.programs import router as programs_router
from handlers.feedback import router as feedback_router
from contacts import router as contacts_router
from services.feedback_service import init_feedback_service


# Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Подключение маршрутизаторов
dp.include_router(schedule_router)  # Расписание
dp.include_router(mfc_services_router)  # МФЦ услуги
dp.include_router(scholarships_router)  # Стипендии
dp.include_router(dormitories_router)  # Общежития
dp.include_router(projects_router)  # Студенческие проекты
dp.include_router(events_router)  # Мероприятия
dp.include_router(programs_router)  # Программы обучения
dp.include_router(feedback_router)  # Обратная связь
dp.include_router(contacts_router)  # Контакты
dp.include_router(main_menu_router)  # Главное меню


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
    
    # Валидируем конфигурацию
    config_error = validate_settings()
    if config_error:
        logger.error(config_error)
        raise RuntimeError(config_error)
    
    # Инициализируем системы безопасности
    logger.info("🔒 Инициализируем системы безопасности...")
    asyncio.create_task(rate_limiter.cleanup())
    asyncio.create_task(session_manager.cleanup_expired_sessions())
    
    await set_commands()
    
    # Инициализируем сервисы
    logger.info("📦 Инициализируем сервисы...")
    try:
        await init_events_service()
        await init_programs_data()
        await init_mfc_data()
        await init_scholarships_data()
        await init_dormitories_data()
        await init_feedback_service()
    except Exception as e:
        logger.error(f"⚠️  Ошибка при инициализации сервисов: {e}", exc_info=True)
        # Продолжаем работу даже если не загрузился один из сервисов
    
    logger.info("✅ Бот успешно инициализирован")


async def on_shutdown():
    """Очистка при остановке бота"""
    logger.info("🛑 Бот останавливается...")
    try:
        await bot.session.close()
    except Exception as e:
        logger.error(f"Ошибка при закрытии сессии: {e}")


async def main():
    """Главная функция запуска бота"""
    try:
        # Настраиваем обработку ошибок
        setup_error_handlers(dp)
        
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
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
        raise

