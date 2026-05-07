#!/usr/bin/env python3
"""
Скрипт для автоматического парсинга всех программ обучения МосПолитеха
Спарсивает все 70+ программ с сохранением в кэш
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем родительскую папку в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from services.advanced_programs_parser import advanced_parser
from services.programs_service import programs_service
from utils.logger import logger


async def main():
    """Главная функция парсинга"""
    try:
        logger.info("=" * 50)
        logger.info("🚀 ЗАПУСК ПАРСИНГА ПРОГРАММ ОБРАЗОВАНИЯ МосПолитеха")
        logger.info("=" * 50)
        
        # Запускаем парсинг
        async with advanced_parser:
            programs_data = await advanced_parser.parse_all_programs()
        
        if not programs_data:
            logger.error("❌ Парсинг не выполнен")
            return False
        
        logger.info(f"\n✅ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО:")
        logger.info(f"   📚 Факультетов: {len(programs_data.faculties)}")
        logger.info(f"   📖 Программ: {len(programs_data.programs)}")
        logger.info(f"   🕐 Время обновления: {programs_data.last_updated}")
        
        # Статистика по факультетам
        logger.info("\n📊 СТАТИСТИКА ПО ФАКУЛЬТЕТАМ:")
        for faculty in programs_data.faculties:
            count = len([p for p in programs_data.programs if p.faculty_id == faculty.id])
            if count > 0:
                logger.info(f"   {faculty.name}: {count} программ")
        
        # Показываем примеры программ
        if programs_data.programs:
            logger.info("\n📌 ПРИМЕРЫ ПРОГРАММ:")
            for program in programs_data.programs[:5]:
                logger.info(f"   • {program.title} ({program.code}) - {program.faculty_name}")
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Программы успешно загружены в кэш")
        logger.info("=" * 50)
        
        return True
    
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
