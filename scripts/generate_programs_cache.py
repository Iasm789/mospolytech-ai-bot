#!/usr/bin/env python
"""
Скрипт для создания кэша программ путём парсинга сайта МосПолитеха
"""
import sys
import asyncio
from pathlib import Path

# Добавляем родительский директорий в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.programs_parser import ProgramsParser
from utils.logger import logger

async def create_cache():
    """Создаёт кэш путём парсинга сайта"""
    logger.info("🚀 Начинаем создание кэша программ...")
    
    async with ProgramsParser() as parser:
        # Парсим программы с сайта
        result = await parser.parse_all_programs()
        
        if result:
            # Сохраняем кэш
            parser.save_cache(result)
            
            logger.info(f"\n✅ Кэш успешно создан:")
            logger.info(f"   • Факультеты: {len(result.faculties)}")
            logger.info(f"   • Программы: {len(result.programs)}")
            
            from collections import defaultdict
            stats = defaultdict(int)
            for prog in result.programs:
                stats[prog.faculty_name] += 1
            
            logger.info(f"\n📊 Распределение программ:")
            for faculty, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   • {faculty}: {count}")
        else:
            logger.error("❌ Не удалось спарсить программы")

if __name__ == "__main__":
    asyncio.run(create_cache())
