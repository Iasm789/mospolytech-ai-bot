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


def _log_answer_pipeline_diagnostics() -> None:
    """Явно логирует эффективные настройки приёма ответов (LLM vs FAQ) и типичные ошибки конфигурации."""
    try:
        ai = get_local_ai_service()
        index_size = ai.get_index_size()
    except Exception:
        index_size = -1
    logger.info(
        "⚙️ Пайплайн ответов: ANSWER_PRIORITY=%s | LOCAL_LLM_ENABLED=%s | "
        "LOCAL_LLM_MODEL=%s | LOCAL_LLM_MODELS=%s | SIMPLE=%s | COMPLEX=%s | "
        "LOCAL_LLM_API_URL=%s | чанков Local AI=%s",
        settings.ANSWER_PRIORITY,
        settings.LOCAL_LLM_ENABLED,
        settings.LOCAL_LLM_MODEL,
        ",".join(settings.local_llm_models_list),
        ",".join(settings.local_llm_simple_models_list),
        ",".join(settings.local_llm_complex_models_list),
        settings.LOCAL_LLM_API_URL,
        index_size,
    )
    if settings.ANSWER_PRIORITY == "faq_first":
        logger.warning(
            "⚠️ ANSWER_PRIORITY=faq_first: сначала ищется FAQ, локальная LLM вызывается только если FAQ не дал ответ. "
            "Чтобы сначала шли RAG+LLM, в .env укажите: ANSWER_PRIORITY=llm_first"
        )
    if settings.ANSWER_PRIORITY == "llm_first" and not settings.LOCAL_LLM_ENABLED:
        logger.warning(
            "⚠️ При ANSWER_PRIORITY=llm_first выключен LOCAL_LLM_ENABLED — генерация LLM не выполняется, "
            "используются шаблон или FAQ."
        )
    if index_size == 0:
        logger.warning(
            "⚠️ Local AI: индекс пуст (нет JSON/TXT в docs). answer_async вернёт None — "
            "пользователю может уйти ответ из FAQ, если он настроен."
        )
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
from handlers.aspirantura import router as aspirantura_router, init_aspirantura_data
from handlers.benefits import router as benefits_router
from handlers.question_handler import router as question_router, init_faq
from contacts import router as contacts_router
from services.feedback_service import init_feedback_service
from services.local_ai_service import get_local_ai_service, init_local_ai_service


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
dp.include_router(aspirantura_router)  # Аспирантура
dp.include_router(benefits_router)  # Льготы
dp.include_router(feedback_router)  # Обратная связь
dp.include_router(contacts_router)  # Контакты
dp.include_router(main_menu_router)  # Главное меню
dp.include_router(question_router)  # Система ответов на вопросы (ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ)


async def set_commands():
    """Установка команд бота"""
    try:
        commands = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="menu", description="Главное меню"),
            BotCommand(command="help", description="Справка"),
        ]
        await bot.set_my_commands(commands)
        logger.info("✅ Команды бота успешно установлены")
    except Exception as e:
        logger.warning(f"⚠️  Не удалось установить команды бота: {e}")
        logger.info("ℹ️  Бот будет работать без предустановленных команд")


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
        await init_aspirantura_data()
        await init_feedback_service()
        init_faq()
        init_local_ai_service()
    except Exception as e:
        logger.error(f"⚠️  Ошибка при инициализации сервисов: {e}", exc_info=True)
        # Продолжаем работу даже если не загрузился один из сервисов

    _log_answer_pipeline_diagnostics()

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

