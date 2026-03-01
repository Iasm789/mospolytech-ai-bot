"""
Сервис для управления мероприятиями

Этот модуль обеспечивает загрузку, фильтрацию, поиск и форматирование
информации о мероприятиях МосПолитеха.
"""

import json
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from utils.logger import logger


class EventsService:
    """
    Сервис для работы с мероприятиями
    
    Обеспечивает загрузку, кэширование, поиск и форматирование
    информации о мероприятиях.
    """
    
    # Поддерживаемые категории мероприятий
    CATEGORIES = {
        "education": "🎓 Обучение",
        "careers": "💼 Карьера",
        "competitions": "🏆 Конкурсы",
        "exhibitions": "🖼 Выставки",
        "culture": "🎭 Культура",
        "volunteering": "🤝 Волонтёрство",
        "student_life": "🎉 Студенческая жизнь"
    }
    
    # Разделители для очистки заголовков
    EMOJI_SEPARATORS = '🎤🎭🏆🎪🎓💼🖼🎉🤝'
    
    # Максимальная длина описания в карточке
    MAX_DESCRIPTION_LENGTH = 300
    
    def __init__(self, data_file: str = "docs/events_data.json"):
        self.data_file = Path(data_file)
        self.events: Dict[str, List[Dict]] = {}
        self.categories = self.CATEGORIES
        self._is_loaded = False
        # Lock для защиты от race conditions при одновременной загрузке
        self._load_lock = asyncio.Lock()
        # Запускаем загрузку данных асинхронно
        asyncio.create_task(self._load_events())
    
    async def _load_events(self) -> bool:
        """
        Загрузить события из файла
        
        Returns:
            bool: True если загрузка успешна, False в противном случае
        """
        try:
            if not self.data_file.exists():
                logger.warning(f"⚠️ Файл {self.data_file} не найден. Инициализируем пустые категории.")
                self.events = {cat: [] for cat in self.categories}
                self._is_loaded = True
                return False
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                
            # Валидируем загруженные данные
            if not isinstance(loaded_data, dict):
                logger.error(f"❌ Неверный формат данных в {self.data_file}")
                self.events = {cat: [] for cat in self.categories}
                self._is_loaded = True
                return False
            
            self.events = loaded_data
            self._is_loaded = True
            
            total_events = sum(len(events) for events in self.events.values())
            logger.info(f"✅ Загружено {total_events} мероприятий из {self.data_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка при парсинге JSON: {e}")
            self.events = {cat: [] for cat in self.categories}
            self._is_loaded = True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке мероприятий: {e}", exc_info=True)
            self.events = {cat: [] for cat in self.categories}
            self._is_loaded = True
            return False
    
    async def _ensure_loaded(self) -> None:
        """Убедиться, что данные загружены (потокобезопасно)"""
        if not self._is_loaded:
            # Используем lock для предотвращения race conditions
            async with self._load_lock:
                # Двойная проверка паттерна (double-checked locking)
                if not self._is_loaded:
                    await self._load_events()
    
    async def get_all_events(self) -> Dict[str, List[Dict]]:
        """
        Получить все события из всех категорий
        
        Returns:
            Dict: Словарь где ключи - категории, значения - списки событий
        """
        await self._ensure_loaded()
        return self.events
    
    async def get_events_by_category(self, category: str) -> List[Dict]:
        """
        Получить события конкретной категории
        
        Args:
            category: Идентификатор категории
        
        Returns:
            List: Отсортированный список событий в категории
        """
        await self._ensure_loaded()
        
        events = self.events.get(category, [])
        if not events:
            logger.debug(f"ℹ️ Категория '{category}' не содержит событий")
            return []
        
        # Сортируем события по дате
        return self._sort_events_by_date(events)
    
    def _sort_events_by_date(self, events: List[Dict]) -> List[Dict]:
        """
        Сортировать события по дате в возрастающем порядке
        
        Args:
            events: Список событий для сортировки
        
        Returns:
            List: Отсортированный список
        """
        try:
            def parse_date(event_time: str) -> datetime:
                """Спарсить дату из различных форматов"""
                time_str = str(event_time) if event_time else ""
                
                # События без даты помещаем в конец
                if not time_str or "не указана" in time_str.lower() or "время не указано" in time_str.lower():
                    return datetime(2099, 12, 31)
                
                # Пытаемся найти дату в формате ДД.ММ.YYYY
                date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
                match = re.search(date_pattern, time_str)
                
                if match:
                    try:
                        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        return datetime(year, month, day)
                    except (ValueError, IndexError):
                        pass
                
                # Если формат ДД-ММ-YYYY
                date_pattern_dash = r'(\d{1,2})-(\d{1,2})-(\d{4})'
                match = re.search(date_pattern_dash, time_str)
                if match:
                    try:
                        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        return datetime(year, month, day)
                    except (ValueError, IndexError):
                        pass
                
                # События с неспарсенной датой помещаем в конец
                return datetime(2099, 12, 31)
            
            return sorted(events, key=lambda e: parse_date(e.get('time', '')))
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при сортировке событий: {e}")
            return events
    
    async def get_event_by_id(self, event_id: str) -> Optional[Tuple[Dict, str]]:
        """
        Получить событие по ID
        
        Args:
            event_id: Идентификатор события
        
        Returns:
            Tuple: (событие, категория) или (None, None)
        """
        if not event_id:
            return None, None
        
        await self._ensure_loaded()
        
        for category, events in self.events.items():
            for event in events:
                if event.get('id') == event_id:
                    return event, category
        
        logger.debug(f"ℹ️ Событие '{event_id}' не найдено")
        return None, None
    
    async def search_events(self, query: str) -> List[Tuple[Dict, str]]:
        """
        Найти события по запросу с ранжированием по релевантности
        
        Args:
            query: Поисковый запрос
        
        Returns:
            List: Список (событие, категория) отсортированный по релевантности
        """
        if not query or not query.strip():
            return []
        
        await self._ensure_loaded()
        
        query_lower = query.lower().strip()
        results_with_score: List[Tuple[Tuple[Dict, str], int]] = []
        
        # Разбиваем запрос на слова для поиска
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        for category, events in self.events.items():
            for event in events:
                score = self._calculate_search_score(event, query_lower, query_words)
                
                if score > 0:
                    results_with_score.append(((event, category), score))
        
        # Сортируем по релевантности (больший score = выше)
        results_with_score.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"🔍 Найдено {len(results_with_score)} результатов для '{query}'")
        return [item[0] for item in results_with_score]
    
    def _calculate_search_score(self, event: Dict, query: str, query_words: List[str]) -> int:
        """
        Вычислить релевантность события для поиска
        
        Args:
            event: Событие
            query: Полный поисковый запрос в нижнем регистре
            query_words: Отдельные слова из запроса
        
        Returns:
            int: Релевантность (чем больше, тем лучше)
        """
        score = 0
        
        title = event.get('title', '').lower()
        desc = event.get('desc', '').lower()
        place = event.get('place', '').lower()
        
        # Точное совпадение в названии (высший приоритет)
        if query in title:
            score += 30
        
        # Совпадение отдельных слов в названии
        for word in query_words:
            if word in title:
                score += 10
        
        # Совпадение в описании
        for word in query_words:
            if word in desc:
                score += 3
        
        # Совпадение в месте проведения
        if query in place:
            score += 5
        
        return score
    
    def parse_event_date(self, time_str: str) -> Optional[datetime]:
        """
        Спарсить дату события из строки
        
        Args:
            time_str: Строка с датой/временем
        
        Returns:
            datetime: Распарсенная дата или None
        """
        if not time_str or "не указана" in str(time_str).lower() or "время не указано" in str(time_str).lower():
            return None
        
        time_str = str(time_str).strip()
        
        # Ищем первую дату в формате ДД.ММ.YYYY
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
        """
        Удалить события, прошедшие более N дней назад
        
        Args:
            days: Количество дней (события старше удаляются)
        
        Returns:
            int: Количество удаленных событий
        """
        try:
            await self._ensure_loaded()
            
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
                        title = event.get('title', 'Unknown')
                        logger.warning(
                            f"⚠️ Удалено старое событие (более {days} дней назад - {days_diff} дней): "
                            f"{title} [{event_date.strftime('%d.%m.%Y')}]"
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
            logger.error(f"❌ Ошибка при удалении старых событий: {e}", exc_info=True)
            return 0
    
    async def _save_events(self) -> bool:
        """
        Сохранить события в файл
        
        Returns:
            bool: True если сохранение успешно
        """
        try:
            # Создаем директорию если не существует
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ События сохранены в {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении мероприятий: {e}", exc_info=True)
            return False
    
    def get_category_name(self, category: str) -> str:
        """
        Получить отображаемое название категории
        
        Args:
            category: Идентификатор категории
        
        Returns:
            str: Название с эмодзи
        """
        return self.categories.get(category, category)
    
    def _clean_title(self, title: str) -> str:
        """
        Очистить заголовок от лишних эмодзи в начале
        
        Args:
            title: Исходный заголовок
        
        Returns:
            str: Очищенный заголовок
        """
        return title.lstrip(self.EMOJI_SEPARATORS).strip()
    
    def format_event(self, event: Dict, category: str) -> str:
        """
        Форматировать событие для вывода
        
        Args:
            event: Данные события
            category: Категория события
        
        Returns:
            str: Отформатированная строка
        """
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
        """
        Форматировать событие кратко (одна строка)
        
        Args:
            event: Данные события
            category: Категория события
        
        Returns:
            str: Краткая строка события
        """
        title = event.get('title', 'Без названия')
        time_str = event.get('time', 'Время не указано')
        place = event.get('place', 'Место не указано')
        
        return f"📌 <b>{title}</b>\n🕒 {time_str} | 📍 {place}"
    
    def format_event_card(self, event: Dict, category: str) -> str:
        """
        Форматировать событие как красивую карточку
        
        Args:
            event: Данные события
            category: Категория события
        
        Returns:
            str: Отформатированная карточка события
        """
        title = self._clean_title(event.get('title', 'Без названия'))
        time_str = event.get('time', 'Время не указано').strip()
        place = event.get('place', 'Место не указано').strip()
        desc = event.get('desc', '').strip()
        
        text = "━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"<b>{title}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += f"⏰ <b>Время:</b>\n{time_str}\n\n"
        text += f"📍 <b>Место:</b>\n{place}\n\n"
        text += f"🏷️ <b>Категория:</b> {self.get_category_name(category)}\n\n"
        
        # Описание с лимитом
        if desc:
            desc_preview = desc[:self.MAX_DESCRIPTION_LENGTH]
            if len(desc) > self.MAX_DESCRIPTION_LENGTH:
                desc_preview += "..."
            text += f"📝 <b>Описание:</b>\n{desc_preview}\n\n"
        
        # Ссылка на источник
        telegram_url = event.get('telegram_url', '')
        if telegram_url:
            text += f"🔗 <a href='{telegram_url}'>Посмотреть в Telegram</a>\n"
        
        return text
    
    def format_event_full(self, event: Dict, category: str) -> str:
        """
        Форматировать полную информацию о событии
        
        Args:
            event: Данные события
            category: Категория события
        
        Returns:
            str: Полная информация о событии
        """
        title = self._clean_title(event.get('title', 'Без названия'))
        time_str = event.get('time', 'Время не указано').strip()
        place = event.get('place', 'Место не указано').strip()
        desc = event.get('desc', '').strip()
        source = event.get('source', '')
        telegram_url = event.get('telegram_url', '')
        
        text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"<b>✨ {title}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += f"<b>📅 Дата и время:</b>\n  {time_str}\n\n"
        text += f"<b>📍 Место:</b>\n  {place}\n\n"
        text += f"<b>🏷️ Категория:</b> {self.get_category_name(category)}\n\n"
        
        if desc:
            text += f"<b>📝 Описание:</b>\n{desc}\n\n"
        
        # Источник и ссылка
        if source or telegram_url:
            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            if source:
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
