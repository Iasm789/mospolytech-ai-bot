"""
Сервис для управления мероприятиями
"""

import json
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from utils.logger import logger


class EventsService:
    """Сервис для работы с мероприятиями"""
    
    def __init__(self, data_file: str = "docs/events_data.json"):
        self.data_file = Path(data_file)
        self.events = {}
        self.categories = {
            "education": "🎓 Обучение",
            "careers": "💼 Карьера",
            "competitions": "🏆 Конкурсы",
            "exhibitions": "🖼 Выставки",
            "culture": "🎭 Культура",
            "volunteering": "🤝 Волонтёрство",
            "student_life": "🎉 Студенческая жизнь"
        }
        asyncio.create_task(self._load_events())
    
    async def _load_events(self):
        """Загрузить события из файла"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.events = json.load(f)
                logger.info(f"✅ Загружено мероприятий из {self.data_file}")
            else:
                logger.warning(f"⚠️ Файл {self.data_file} не найден")
                self.events = {cat: [] for cat in self.categories}
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке мероприятий: {e}")
            self.events = {cat: [] for cat in self.categories}
    
    async def get_all_events(self) -> Dict[str, List[Dict]]:
        """Получить все события"""
        # Убедимся, что данные загружены
        if not self.events:
            await self._load_events()
        return self.events
    
    async def get_events_by_category(self, category: str) -> List[Dict]:
        """Получить события по категориям"""
        if not self.events:
            await self._load_events()
        
        # Получаем события из указанной категории
        events = self.events.get(category, [])
        
        # Сортируем по дате (попытаемся спарсить дату)
        return self._sort_events_by_date(events)
    
    def _sort_events_by_date(self, events: List[Dict]) -> List[Dict]:
        """Сортировать события по дате с улучшенным парсингом"""
        try:
            def parse_date(event_time: str) -> datetime:
                """Попытаться спарсить дату из строки с поддержкой многих форматов"""
                time_str = str(event_time) if not isinstance(event_time, str) else event_time
                
                if "не указана" in time_str.lower() or "время не указано" in time_str.lower():
                    return datetime(2099, 12, 31)  # Неизвестные дата ставим в конец
                
                # Форматы которые мы проверяем:
                # 1. ДД.ММ.YYYY (классический формат)
                # 2. ДД.ММ.YYYY HH:MM
                # 3. ДД-ММ-YYYY
                # 4. YYYY-MM-DD
                
                parts = time_str.split()
                
                for part in parts:
                    # Проверяем формат ДД.ММ.YYYY
                    if '.' in part and len(part) >= 10:
                        try:
                            date_part = part.split()[0] if ' ' in part else part
                            if date_part.count('.') == 2:
                                day, month, year = date_part.split('.')
                                return datetime(int(year), int(month), int(day))
                        except (ValueError, IndexError):
                            pass
                    
                    # Проверяем формат ДД-ММ-YYYY
                    if '-' in part and len(part) >= 8:
                        try:
                            date_parts = part.split('-')
                            if len(date_parts) == 3:
                                # Определяем какой формат: ДД-ММ-YYYY или YYYY-ММ-ДД
                                if int(date_parts[0]) > 31:
                                    # YYYY-MM-DD
                                    return datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                                else:
                                    # DD-MM-YYYY
                                    return datetime(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))
                        except (ValueError, IndexError):
                            pass
                
                # Если не смогли спарсить дату, возвращаем текущую дату
                return datetime(2099, 12, 31)
            
            return sorted(events, key=lambda e: parse_date(e.get('time', '')))
        except Exception as e:
            logger.error(f"❌ Ошибка при сортировке событий: {e}")
            return events
    
    async def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Получить событие по ID"""
        if not self.events:
            await self._load_events()
        
        for category, events in self.events.items():
            for event in events:
                if event.get('id') == event_id:
                    return event, category
        
        return None, None
    
    async def search_events(self, query: str) -> List[tuple]:
        """Найти события по запросу с улучшенным поиском и ранжированием"""
        if not self.events:
            await self._load_events()
        
        query_lower = query.lower()
        results_with_score = []
        
        # Разбиваем запрос на отдельные слова для более гибкого поиска
        query_words = query_lower.split()
        
        for category, events in self.events.items():
            for event in events:
                title = event.get('title', '').lower()
                desc = event.get('desc', '').lower()
                place = event.get('place', '').lower()
                
                score = 0
                
                # Проверяем точное совпадение в названии (высший приоритет)
                if query_lower in title:
                    score += 10
                
                # Проверяем совпадение отдельных слов в названии
                for word in query_words:
                    if len(word) > 2:  # Игнорируем предлоги и короткие слова
                        if word in title:
                            score += 3
                
                # Проверяем совпадение в описании
                for word in query_words:
                    if len(word) > 2:
                        if word in desc:
                            score += 1
                
                # Проверяем совпадение в месте проведения
                if query_lower in place:
                    score += 2
                
                # Если есть хоть какое-то совпадение, добавляем в результаты
                if score > 0:
                    results_with_score.append(((event, category), score))
        
        # Сортируем по релевантности (больший score = выше в списке)
        results_with_score.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем только события без scores
        return [item[0] for item in results_with_score]
    
    def parse_event_date(self, time_str: str) -> Optional[datetime]:
        """Спарсить дату события из строки"""
        if not time_str or "не указана" in time_str.lower() or "время не указано" in time_str.lower():
            return None
        
        time_str = str(time_str).strip()
        
        # Извлекаем первую дату из строки (может быть диапазон типа "24.11.2025 по 28.11.2025")
        # Ищем первое число в формате ДД.ММ.YYYY
        date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        match = re.search(date_pattern, time_str)
        
        if match:
            try:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return datetime(year, month, day)
            except (ValueError, IndexError):
                pass
        
        return None
    
    async def remove_old_events(self, days: int = 30) -> int:
        """Удалить события, которые были более N дней назад"""
        try:
            if not self.events:
                await self._load_events()
            
            removed_count = 0
            current_date = datetime.now()
            
            for category in self.events:
                remaining_events = []
                
                for event in self.events[category]:
                    event_date = self.parse_event_date(event.get('time', ''))
                    
                    if event_date is None:
                        # Если дату не можем спарсить, оставляем событие
                        remaining_events.append(event)
                        continue
                    
                    # Вычисляем разницу в днях
                    days_diff = (current_date - event_date).days
                    
                    if days_diff > days:
                        logger.warning(
                            f"⚠️ Удалено старое событие (более {days} дней назад - {days_diff} дней): "
                            f"{event.get('title')} [{event_date.strftime('%d.%m.%Y')}]"
                        )
                        removed_count += 1
                    else:
                        remaining_events.append(event)
                
                self.events[category] = remaining_events
            
            if removed_count > 0:
                logger.info(f"✅ Удалено {removed_count} старых событий (более {days} дней)")
                await self._save_events()
            
            return removed_count
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении старых событий: {e}")
            return 0
    
    async def _save_events(self):
        """Сохранить события в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ События сохранены в {self.data_file}")
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении мероприятий: {e}")
    
    def get_category_name(self, category: str) -> str:
        """Получить название категории"""
        return self.categories.get(category, category)
    
    def format_event(self, event: Dict, category: str) -> str:
        """Форматировать событие для вывода"""
        title = event.get('title', 'Без названия')
        time_str = event.get('time', 'Время не указано')
        place = event.get('place', 'Место не указано')
        desc = event.get('desc', '')
        event_id = event.get('id', '')
        
        # Обрезаем описание, если слишком длинное
        if len(desc) > 200:
            desc = desc[:200] + "..."
        
        text = (
            f"📌 <b>{title}</b>\n\n"
            f"🕒 <b>Время:</b> {time_str}\n"
            f"📍 <b>Место:</b> {place}\n"
            f"🏷 <b>Категория:</b> {self.get_category_name(category)}\n"
        )
        
        if desc:
            text += f"\n📝 <b>Описание:</b>\n{desc}\n"
        
        if event_id:
            text += f"\n🔑 ID: {event_id}"
        
        return text
    
    def format_event_short(self, event: Dict, category: str) -> str:
        """Форматировать событие кратко"""
        title = event.get('title', 'Без названия')
        time_str = event.get('time', 'Время не указано')
        place = event.get('place', 'Место не указано')
        event_id = event.get('id', '')
        
        text = f"📌 <b>{title}</b>\n"
        text += f"🕒 {time_str} | 📍 {place}\n"
        
        if event_id:
            text += f"ID: {event_id}"
        
        return text
    
    def format_event_card(self, event: Dict, category: str) -> str:
        """Форматировать событие как красивую карточку"""
        title = event.get('title', 'Без названия').strip()
        time_str = event.get('time', 'Время не указано').strip()
        place = event.get('place', 'Место не указано').strip()
        desc = event.get('desc', '').strip()
        
        # Очищаем заголовок от лишних эмодзи, если они повторяются в категории
        title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
        
        # Создаем красивую карточку
        text = "━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"<b>{title}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Время
        text += f"⏰ <b>Время:</b>\n{time_str}\n\n"
        
        # Место
        text += f"📍 <b>Место:</b>\n{place}\n\n"
        
        # Категория
        text += f"🏷️ <b>Категория:</b> {self.get_category_name(category)}\n\n"
        
        # Описание (максимум 300 символов)
        if desc:
            desc_preview = desc[:300]
            if len(desc) > 300:
                desc_preview += "..."
            text += f"📝 <b>Описание:</b>\n{desc_preview}\n\n"
        
        # Ссылка на источник
        telegram_url = event.get('telegram_url', '')
        if telegram_url:
            text += f"🔗 <a href='{telegram_url}'>Посмотреть в Telegram</a>\n"
        
        return text
    
    def format_event_full(self, event: Dict, category: str) -> str:
        """Форматировать полную информацию о событии"""
        title = event.get('title', 'Без названия').strip()
        time_str = event.get('time', 'Время не указано').strip()
        place = event.get('place', 'Место не указано').strip()
        desc = event.get('desc', '').strip()
        source = event.get('source', '')
        telegram_url = event.get('telegram_url', '')
        confidence = event.get('confidence', 0.8)
        
        # Очищаем заголовок от лишних эмодзи
        title = title.lstrip('🎤🎭🏆🎪🎓💼🖼🎉🤝')
        
        text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"<b>✨ {title}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Дата и время
        text += f"<b>📅 Дата и время:</b>\n  {time_str}\n\n"
        
        # Место проведения
        text += f"<b>📍 Место:</b>\n  {place}\n\n"
        
        # Категория
        text += f"<b>🏷️ Категория:</b> {self.get_category_name(category)}\n\n"
        
        # Полное описание
        if desc:
            text += f"<b>📝 Описание:</b>\n{desc}\n\n"
        
        # Источник и ссылка
        if source or telegram_url:
            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            if source:
                # Улучшаем читаемость источника
                source_display = source.replace('_v2_events', '').replace('_', ' ').title()
                text += f"<b>📢 Источник:</b> {source_display}\n"
            if telegram_url:
                text += f"<b>🔗 Ссылка:</b> <a href='{telegram_url}'>Перейти в Telegram</a>\n"
        
        return text


# Глобальный экземпляр сервиса
_events_service = None


async def init_events_service():
    """Инициализировать сервис мероприятий"""
    global _events_service
    _events_service = EventsService()
    await _events_service._load_events()
    return _events_service


def get_events_service() -> EventsService:
    """Получить сервис мероприятий"""
    global _events_service
    if _events_service is None:
        _events_service = EventsService()
    return _events_service
