#!/usr/bin/env python3
"""
Генератор реальных данных программ обучения МосПолитеха (2025-2026)
Интегрирует гибридный парсер для получения достоверных данных с сайта
Никогда не использует ненадежные или придуманные от себя данные!
"""

import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Попытка импортировать новый парсер
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from parse_hybrid import HybridMosPolyParser
    PARSER_AVAILABLE = True
    logger.info("✅ Гибридный парсер успешно загружен")
except ImportError as e:
    PARSER_AVAILABLE = False
    logger.warning(f"⚠️  Гибридный парсер недоступен: {e}")


def _load_cached_programs() -> Optional[List[Dict]]:
    """Загрузить программы из кэша если он существует"""
    cache_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            programs = data.get('programs', [])
            if programs:
                logger.info(f"✅ Загружены программы из кэша: {len(programs)} программ")
                return programs
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при чтении кэша: {e}")
    
    return None


async def generate_programs_cache(force_parse: bool = False) -> bool:
    """
    Генерировать и сохранить кэш программ
    
    Args:
        force_parse: Если True, всегда запускает парсер вместо использования кэша
    """
    cache_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    programs = None
    
    # Стратегия 1: Попытка использовать реальный парсер
    if PARSER_AVAILABLE and force_parse:
        try:
            logger.info("\n" + "=" * 80)
            logger.info("🚀 СТРАТЕГИЯ 1: Запуск гибридного парсера для получения актуальных данных")
            logger.info("=" * 80)
            
            parser = HybridMosPolyParser()
            success = await parser.parse_complete()
            
            if success:
                programs = parser.get_programs_list()
                logger.info(f"✅ Парсер успешно получил {len(programs)} программ!")
                parser.save_cache(cache_file)
                
                return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсера: {e}. Попробую альтернативный способ...")
    
    # Стратегия 2: Загрузить из кэша если он существует
    if not force_parse:
        logger.info("\n" + "=" * 80)
        logger.info("🔄 СТРАТЕГИЯ 2: Загрузка программ из локального кэша")
        logger.info("=" * 80)
        
        programs = _load_cached_programs()
        if programs:
            # Сохраняем с обновленной датой
            faculties_summary = {}
            for prog in programs:
                fac = prog.get('faculty_name', 'Неизвестный')
                if fac not in faculties_summary:
                    faculties_summary[fac] = 0
                faculties_summary[fac] += 1
            
            result = {
                'source': 'https://mospolytech.ru/postupayushchim/programmy-obucheniya/bakalavriat/',
                'programs': programs,
                'statistics': {
                    'total_programs': len(programs),
                    'by_faculty': faculties_summary,
                },
                'last_updated': datetime.now().isoformat(),
                'note': 'Данные получены путем парсинга официального сайта МосПолитеха. '
                       'Используется кэширована версия. Запустите с параметром --force для обновления.',
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n✅ Сохранены программы:")
            logger.info(f"   Всего: {len(programs)}")
            for fac, count in sorted(faculties_summary.items()):
                logger.info(f"   - {fac}: {count}")
            
            return True
    
    # Если ничего не удалось загрузить
    logger.error("\n❌ ОШИБКА: Не удалось загрузить программы")
    logger.error("   - Парсер недоступен")
    logger.error("   - Кэш отсутствует или поврежден")
    logger.error("\nДействия:")
    logger.error("  1. Убедитесь что установлен Playwright:")
    logger.error("     pip install playwright && playwright install chromium")
    logger.error("  2. Запустите парсер со следующей командой:")
    logger.error("     python scripts/parse_hybrid.py")
    
    return False


async def main():
    """Главная функция"""
    import argparse
    
    p = argparse.ArgumentParser(description='Генератор программ МосПолитеха')
    p.add_argument('--force', action='store_true', 
                   help='Принудительно запустить парсер вместо использования кэша')
    p.add_argument('--parser-only', action='store_true',
                   help='Только запустить парсер')
    
    args = p.parse_args()
    
    if args.parser_only and PARSER_AVAILABLE:
        # Только запуск парсера
        logger.info("🚀 Запуск парсера...")
        parser = HybridMosPolyParser()
        success = await parser.parse_complete()
        if success:
            parser.save_cache()
        return success
    
    # Генерация кэша
    success = await generate_programs_cache(force_parse=args.force)
    
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ УСПЕШНО: Программы готовы к использованию")
        logger.info(f"   Файл: data/cache/programs_cache.json")
    else:
        logger.info("❌ ОШИБКА: Необходимо вручную запустить парсер")
        if PARSER_AVAILABLE:
            logger.info("   python scripts/parse_hybrid.py")
    logger.info("=" * 80)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
