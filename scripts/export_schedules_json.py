"""
Экспорт расписаний всех групп в красивый JSON файл
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.schedule_parser import ScheduleParser
from utils.logger import logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)


def convert_schedule_to_dict(schedule_data: dict) -> dict:
    """
    Конвертирует расписание в формат для сохранения в JSON
    
    Args:
        schedule_data: Данные расписания из parser.get_schedule_by_group()
        
    Returns:
        Отформатированный словарь расписания
    """
    if not schedule_data:
        return None
    
    try:
        formatted = {
            "group": schedule_data.get('group'),
            "group_info": schedule_data.get('group_info', {}),
            "days": {}
        }
        
        # Форматируем дни недели
        for day_name, day_info in schedule_data.get('days', {}).items():
            lessons = []
            
            for lesson in day_info.get('lessons', []):
                lesson_dict = {
                    "time": lesson.get('time_str', ''),
                    "type": lesson.get('type', ''),
                    "subject": lesson.get('subject', ''),
                    "classrooms": lesson.get('classrooms', []),
                    "teacher": lesson.get('teacher', ''),
                    "period": lesson.get('period', ''),
                    "webinar_url": lesson.get('webinar_url')
                }
                lessons.append(lesson_dict)
            
            formatted["days"][day_name] = {
                "lessons": lessons
            }
        
        return formatted
    except Exception as e:
        logger.error(f"Ошибка при конвертации расписания: {e}")
        return None


def export_all_schedules(output_file: str = None):
    """
    Экспортирует расписания всех групп в JSON файл
    
    Args:
        output_file: Путь к файлу для сохранения (по умолчанию: data/all_schedules.json)
    """
    if output_file is None:
        output_file = project_root / 'data' / 'all_schedules.json'
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("🚀 Начинаем экспорт расписаний всех групп...")
    logger.info(f"📁 Файл будет сохранён: {output_file}")
    
    # Инициализируем парсер
    parser = ScheduleParser()
    
    # Получаем все группы
    all_groups = parser._all_groups
    if not all_groups:
        logger.error("❌ Список групп пуст!")
        return False
    
    logger.info(f"📊 Всего групп для обработки: {len(all_groups)}")
    
    all_schedules = {}
    successful = 0
    failed = 0
    
    # Получаем расписание для каждой группы
    for idx, group in enumerate(sorted(all_groups), 1):
        try:
            if idx % 50 == 0:
                logger.info(f"⏳ Обработано {idx}/{len(all_groups)} групп...")
            
            schedule_data = parser.get_schedule_by_group(group)
            
            if schedule_data:
                formatted = convert_schedule_to_dict(schedule_data)
                if formatted:
                    all_schedules[group] = formatted
                    successful += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при обработке группы {group}: {e}")
            failed += 1
    
    # Сохраняем в JSON с красивым форматированием
    try:
        logger.info(f"💾 Сохраняем {successful} расписаний в JSON...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                all_schedules,
                f,
                ensure_ascii=False,
                indent=2,
                default=str  # Для сериализации объектов типа datetime
            )
        
        file_size = output_file.stat().st_size / (1024 * 1024)  # Размер в МБ
        logger.info(f"✅ Успешно экспортировано {successful} расписаний")
        logger.info(f"❌ Ошибок при обработке: {failed}")
        logger.info(f"📊 Размер файла: {file_size:.2f} МБ")
        logger.info(f"🎉 Файл сохранён: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла: {e}")
        return False


def export_prettified_schedules(output_file: str = None):
    """
    Экспортирует расписания в красивом текстовом формате + JSON
    
    Args:
        output_file: Путь к файлу для сохранения JSON
    """
    if output_file is None:
        output_file = project_root / 'data' / 'schedules_pretty.json'
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("🎨 Начинаем экспорт расписаний в красивом формате...")
    
    # Инициализируем парсер
    parser = ScheduleParser()
    all_groups = parser._all_groups
    
    if not all_groups:
        logger.error("❌ Список групп пуст!")
        return False
    
    logger.info(f"📊 Всего групп для обработки: {len(all_groups)}")
    
    pretty_schedules = {}
    successful = 0
    
    # Получаем красиво отформатированное расписание
    for idx, group in enumerate(sorted(all_groups), 1):
        try:
            if idx % 50 == 0:
                logger.info(f"⏳ Обработано {idx}/{len(all_groups)} групп...")
            
            # Получаем красивый текстовый формат
            pretty_text = parser.get_schedule_by_group_pretty(group)
            
            if pretty_text and "❌" not in pretty_text:
                pretty_schedules[group] = pretty_text
                successful += 1
                
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при обработке группы {group}: {e}")
    
    # Сохраняем в JSON
    try:
        logger.info(f"💾 Сохраняем {successful} расписаний в красивом формате...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                pretty_schedules,
                f,
                ensure_ascii=False,
                indent=2
            )
        
        file_size = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Успешно экспортировано {successful} расписаний в красивом формате")
        logger.info(f"📊 Размер файла: {file_size:.2f} МБ")
        logger.info(f"🎉 Файл сохранён: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла: {e}")
        return False


if __name__ == "__main__":
    import time
    
    print("\n" + "="*60)
    print("📅 ЭКСПОРТ РАСПИСАНИЙ ВСЕХ ГРУПП")
    print("="*60 + "\n")
    
    start_time = time.time()
    
    print("Выберите формат экспорта:")
    print("1. Структурированный JSON (быстрее, надёжнее)")
    print("2. Красивый текстовый формат")
    print("3. Обе версии")
    print()
    
    # Если запустить без аргументов, по умолчанию экспортируем структурированный JSON
    choice = input("Выберите (1-3) [по умолчанию 1]: ").strip() or "1"
    
    try:
        choice = int(choice)
    except ValueError:
        choice = 1
    
    if choice in (1, 3):
        print("\n🔄 Экспортирую структурированный JSON...\n")
        export_all_schedules()
    
    if choice in (2, 3):
        print("\n🔄 Экспортирую красивый формат...\n")
        export_prettified_schedules()
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Время выполнения: {elapsed:.2f} секунд")
    print("="*60 + "\n")
