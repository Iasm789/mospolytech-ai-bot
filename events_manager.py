#!/usr/bin/env python3
"""
Интеграция расширенного парсера в основной процесс
Использует все улучшенные функции для поддержания качества данных
"""

import asyncio
from datetime import datetime
from services.events_parser import EventsParser
from utils.logger import logger


class EventsManager:
    """Менеджер для автоматического управления мероприятиями"""
    
    def __init__(self):
        self.parser = EventsParser()
    
    def initialize(self):
        """Инициализировать менеджер"""
        logger.info("🚀 Инициализация EventsManager...")
        self.parser.load_events()
        logger.info("✅ EventsManager готов к работе")
    
    def maintenance_run(self):
        """Выполнить полное техническое обслуживание"""
        logger.info("🔧 Запуск полного обслуживания мероприятий...")
        
        # 1. Удаление старых событий
        logger.info("   1️⃣ Удаление старых мероприятий (>30 дней)...")
        removed_old = self.parser.remove_old_events(days=30)
        
        # 2. Очистка дубликатов
        logger.info("   2️⃣ Очистка дубликатов и неполных записей...")
        removed_dups = self.parser.clean_events()
        
        # 3. Валидация всех событий
        logger.info("   3️⃣ Валидация данных всех мероприятий...")
        validation_issues = self._validate_all_events()
        
        # 4. Поиск потенциальных дубликатов
        logger.info("   4️⃣ Поиск потенциальных дубликатов...")
        duplicates = self.parser.find_duplicate_candidates(similarity_threshold=0.8)
        
        # 5. Экспорт для резервной копии
        logger.info("   5️⃣ Создание резервной копии...")
        backup_file = f"backup_events_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self.parser.export_to_csv(backup_file)
        
        # Отчет
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 ОТЧЕТ ОБ ОБСЛУЖИВАНИИ")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Удалено старых событий: {removed_old}")
        logger.info(f"✅ Удалено дубликатов: {removed_dups}")
        logger.info(f"⚠️  Проблем с валидацией: {validation_issues}")
        logger.info(f"⚠️  Потенциальных дубликатов: {len(duplicates)}")
        logger.info(f"💾 Резервная копия: {backup_file}")
        logger.info(f"{'='*60}\n")
    
    def print_upcoming_summary(self):
        """Вывести краткую справку по предстоящим событиям"""
        upcoming = self.parser.get_upcoming_events(days_ahead=7)
        
        logger.info(f"\n📅 ПРЕДСТОЯЩИЕ СОБЫТИЯ (7 ДНЕЙ)")
        logger.info("="*60)
        
        if not upcoming:
            logger.info("✅ Нет мероприятий на неделю")
        else:
            total = sum(len(events) for events in upcoming.values())
            logger.info(f"🎯 Всего событий: {total}\n")
            
            for category, events in upcoming.items():
                cat_name = self.parser.categories.get(category, category)
                logger.info(f"{cat_name}: {len(events)} событий")
                for event in events:
                    date = self.parser.parse_event_date(event.get('time', ''))
                    date_str = date.strftime('%d.%m.%Y') if date else '?'
                    logger.info(f"  • {event.get('title')} [{date_str}]")
        
        logger.info("="*60 + "\n")
    
    def get_statistics(self) -> dict:
        """Получить полную статистику"""
        return self.parser.get_advanced_statistics()
    
    def print_full_report(self):
        """Вывести полный отчет о состоянии мероприятий"""
        logger.info("\n" + "="*70)
        logger.info("📊 ПОЛНЫЙ ОТЧЕТ О СОСТОЯНИИ МЕРОПРИЯТИЙ")
        logger.info("="*70 + "\n")
        
        # Статистика
        self.parser.print_statistics()
        
        # Предстоящие события
        self.print_upcoming_summary()
        
        # Дополнительная информация
        stats = self.get_statistics()
        logger.info("📈 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
        logger.info(f"   Среднее качество данных: {stats['average_confidence']*100:.1f}%")
        logger.info(f"   События на 30 дней: {stats['upcoming_30days']}")
        
    def _validate_all_events(self) -> int:
        """Валидировать все события и вернуть количество проблем"""
        issues_count = 0
        
        for category, events in self.parser.events.items():
            for event in events:
                is_valid, errors = self.parser.validate_event_data(event)
                if not is_valid:
                    issues_count += 1
                    logger.warning(f"   ⚠️ {event.get('title')}: {', '.join(errors)}")
        
        return issues_count


def main():
    """Главная функция для демонстрации всех функций"""
    print("\n" + "🌟"*35)
    print("🚀 ЗАПУСК РАСШИРЕННОГО МЕНЕДЖЕРА МЕРОПРИЯТИЙ")
    print("🌟"*35)
    
    manager = EventsManager()
    manager.initialize()
    
    # Полное обслуживание
    manager.maintenance_run()
    
    # Полный отчет
    manager.print_full_report()
    
    print("\n" + "✨"*35)
    print("🎉 МЕНЕДЖЕР ЗАВЕРШИЛ РАБОТУ!")
    print("✨"*35 + "\n")


if __name__ == "__main__":
    main()
