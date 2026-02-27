#!/usr/bin/env python3
"""
Скрипт инициализации мероприятий МосПолитеха
Можно запустить вручную для обновления и добавления новых событий
"""

import sys
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from services.events_parser import EventsParser
from utils.logger import logger


async def init_events():
    """Инициализировать и обновить события"""
    logger.info("🎪 Инициализация мероприятий...")
    
    parser = EventsParser()
    parser.load_events()
    parser.print_statistics()
    
    return True


def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🎪 ИНИЦИАЛИЗАЦИЯ МЕРОПРИЯТИЙ МОСПОЛИТЕХА")
    print("="*60)
    
    parser = EventsParser()
    
    # Загружаем события
    parser.load_events()
    
    # Выводим текущую статистику
    print("\n📊 Текущая статистика:")
    parser.print_statistics()
    
    # Попытаемся добавить новые события
    print("📝 Проверка и добавление новых примеров мероприятий...")
    if parser.add_sample_events():
        print("✅ Примеры мероприятий обновлены!")
    else:
        print("⚠️ Не удалось добавить примеры мероприятий")
    
    # Выводим финальную статистику
    print("\n📊 Финальная статистика:")
    parser.print_statistics()
    
    print("✅ Инициализация завершена!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
