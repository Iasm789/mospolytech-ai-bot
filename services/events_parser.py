"""
Парсер мероприятий из источников (ручное добавление и обновление)
"""

import json
import asyncio
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import uuid

from utils.logger import logger


class EventsParser:
    """Парсер мероприятий с расширенным функционалом и оптимизацией"""
    
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
        
        # Кэширование результатов
        self._cache = {
            "all_events": None,
            "search_results": {},
            "upcoming_events": None,
            "cache_time": {}
        }
        self.cache_ttl = 300  # 5 минут
        
        # Ключевые слова для автоматической категоризации
        self.category_keywords = {
            "education": ["обучение", "мастер-класс", "лекция", "семинар", "тренинг", "курс", "webinar", "вебинар", "подготовка", "школа"],
            "careers": ["карьер", "job", "работ", "собеседование", "intern", "стажер", "работодатель", "hr", "рекрутинг", "компани"],
            "competitions": ["конкурс", "соревнован", "чемпион", "олимпиад", "турнир", "марафон", "челленж", "challenge"],
            "culture": ["концерт", "выставка", "театр", "кино", "музык", "искусств", "танец", "пение", "культур", "арт"],
            "volunteering": ["волонтер", "добровольч", "помощь", "благотворит", "социал", "волонтёр"],
            "student_life": ["студенч", "вечеринк", "вечер", "пати", "гулянк", "развлечен", "жизнь", "друж", "общежи"]
        }
    
    def detect_category_from_title(self, title: str) -> Optional[str]:
        """Определить категорию на основе заголовка события"""
        title_lower = title.lower()
        
        # Подсчитываем совпадения ключевых слов для каждой категории
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in title_lower:
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        # Возвращаем категорию с наивысшим score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def detect_category_from_description(self, title: str, description: str) -> Optional[str]:
        """Определить категорию на основе описания события"""
        combined_text = (title + " " + description).lower()
        
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # Каждое совпадение добавляет очки
                score += combined_text.count(keyword)
            if score > 0:
                category_scores[category] = score
        
        # Возвращаем категорию с наивысшим score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def auto_categorize_event(self, title: str, desc: str = "", source: str = "") -> str:
        """Автоматически категоризировать событие"""
        # Сначала пытаемся определить по заголовку
        category = self.detect_category_from_title(title)
        
        if not category:
            # Если не получилось, пытаемся по описанию
            category = self.detect_category_from_description(title, desc)
        
        # Если все еще не определено, возвращаем student_life как default
        if not category:
            category = "student_life"
        
        return category
    
    def load_events(self) -> Dict:
        """Загрузить события из файла"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.events = json.load(f)
                logger.info(f"✅ Загружено мероприятий из {self.data_file}")
                return self.events
            else:
                logger.warning(f"⚠️ Файл {self.data_file} не найден, создаём новый")
                self.events = {cat: [] for cat in self.categories}
                self.save_events()
                return self.events
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке мероприятий: {e}")
            self.events = {cat: [] for cat in self.categories}
            return self.events
    
    def save_events(self) -> bool:
        """Сохранить события в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ События сохранены в {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении мероприятий: {e}")
            return False
    
    def add_event(self, 
                  category: str,
                  title: str,
                  time: str,
                  place: str,
                  desc: str,
                  source: str,
                  telegram_url: str,
                  event_id: Optional[str] = None,
                  confidence: float = 0.9,
                  auto_categorize: bool = False) -> bool:
        """Добавить новое событие с опциональной автокатегоризацией"""
        try:
            # Если auto_categorize включен, определяем категорию автоматически
            if auto_categorize:
                detected_category = self.auto_categorize_event(title, desc, source)
                if detected_category:
                    category = detected_category
            
            if category not in self.events:
                logger.error(f"❌ Неизвестная категория: {category}")
                return False
            
            # Валидация и очистка данных
            if not title or not title.strip():
                logger.error("❌ Название события не может быть пустым")
                return False
            
            event = {
                "id": event_id or str(uuid.uuid4())[:8],
                "title": title.strip(),
                "time": time.strip() if time else "Время не указано",
                "place": place.strip() if place else "Место не указано",
                "desc": desc.strip(),
                "source": source.strip() if source else "unknown",
                "telegram_url": telegram_url.strip() if telegram_url else "",
                "confidence": min(confidence, 1.0)  # Уверенность не больше 1.0
            }
            
            # Проверяем на дубликаты по заголовку (игнорируя регистр)
            for existing_event in self.events[category]:
                if existing_event.get("title", "").lower() == title.lower():
                    logger.warning(f"⚠️ Событие с таким названием уже существует: {title}")
                    return False
            
            self.events[category].append(event)
            logger.info(f"✅ Добавлено событие: {title}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении события: {e}")
            return False
    
    def update_event(self, 
                     category: str,
                     event_id: str,
                     **kwargs) -> bool:
        """Обновить событие"""
        try:
            if category not in self.events:
                logger.error(f"❌ Неизвестная категория: {category}")
                return False
            
            for event in self.events[category]:
                if event.get('id') == event_id:
                    event.update(kwargs)
                    logger.info(f"✅ Обновлено событие с ID: {event_id}")
                    return True
            
            logger.error(f"❌ Событие с ID {event_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении события: {e}")
            return False
    
    def remove_event(self, category: str, event_id: str) -> bool:
        """Удалить событие"""
        try:
            if category not in self.events:
                logger.error(f"❌ Неизвестная категория: {category}")
                return False
            
            for idx, event in enumerate(self.events[category]):
                if event.get('id') == event_id:
                    self.events[category].pop(idx)
                    logger.info(f"✅ Удалено событие с ID: {event_id}")
                    return True
            
            logger.error(f"❌ Событие с ID {event_id} не найдено")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении события: {e}")
            return False
    
    def get_events_count(self) -> Dict[str, int]:
        """Получить количество событий по категориям"""
        counts = {}
        for category, events in self.events.items():
            counts[category] = len(events)
        return counts
    
    def validate_events(self) -> Dict[str, List[str]]:
        """Валидировать события и вернуть список ошибок"""
        issues = {}
        
        for category, events in self.events.items():
            category_issues = []
            
            for idx, event in enumerate(events):
                # Проверяем обязательные поля
                if not event.get("id"):
                    category_issues.append(f"Событие {idx}: отсутствует ID")
                
                if not event.get("title"):
                    category_issues.append(f"Событие {idx}: отсутствует заголовок")
                
                if not event.get("time"):
                    category_issues.append(f"Событие {idx} ({event.get('title', 'Unknown')}): отсутствует время")
                
                # Проверяем на дубликаты в одной категории
                for other_idx, other_event in enumerate(events[idx+1:], start=idx+1):
                    if event.get("title", "").lower() == other_event.get("title", "").lower():
                        category_issues.append(f"Дубликат: события {idx} и {other_idx} имеют одинаковые названия")
            
            if category_issues:
                issues[category] = category_issues
        
        return issues
    
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
    
    def remove_old_events(self, days: int = 30) -> int:
        """Удалить события, которые были более N дней назад"""
        try:
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
                self.save_events()
            
            return removed_count
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении старых событий: {e}")
            return 0
    
    def clean_events(self) -> int:
        """Очистить события от дубликатов и неполных записей"""
        removed_count = 0
        
        for category in self.events:
            seen_titles = set()
            cleaned_events = []
            
            for event in self.events[category]:
                # Проверяем наличие обязательных полей
                if not event.get("id") or not event.get("title") or not event.get("time"):
                    logger.warning(f"⚠️ Удалено неполное событие: {event.get('title', 'Unknown')}")
                    removed_count += 1
                    continue
                
                title_lower = event.get("title", "").lower()
                
                # Проверяем на дубликаты
                if title_lower in seen_titles:
                    logger.warning(f"⚠️ Удален дубликат: {event.get('title')}")
                    removed_count += 1
                    continue
                
                seen_titles.add(title_lower)
                cleaned_events.append(event)
            
            self.events[category] = cleaned_events
        
        if removed_count > 0:
            logger.info(f"✅ Удалено {removed_count} некорректных событий")
            self.save_events()
        
        return removed_count
    
    def find_duplicate_candidates(self, similarity_threshold: float = 0.7) -> List[Tuple[Dict, Dict, str]]:
        """Найти потенциальные дубликаты по сходству названия и даты"""
        from difflib import SequenceMatcher
        
        duplicates = []
        seen_pairs = set()
        
        for category, events in self.events.items():
            for i, event1 in enumerate(events):
                for j, event2 in enumerate(events[i+1:], start=i+1):
                    # Проверяем не проверяли ли мы эту пару уже
                    pair_key = (event1.get('id'), event2.get('id'))
                    if pair_key in seen_pairs:
                        continue
                    
                    # Сравниваем названия
                    title1 = event1.get('title', '').lower()
                    title2 = event2.get('title', '').lower()
                    
                    similarity = SequenceMatcher(None, title1, title2).ratio()
                    
                    # Если сходство больше порога, добавляем как потенциальный дубликат
                    if similarity >= similarity_threshold:
                        duplicates.append((event1, event2, category))
                        seen_pairs.add(pair_key)
        
        return duplicates
    
    def get_upcoming_events(self, days_ahead: int = 7) -> Dict[str, List[Dict]]:
        """Получить предстоящие мероприятия на N дней вперед"""
        # Проверяем кэш
        cache_key = f"upcoming_{days_ahead}"
        if cache_key in self._cache and self._check_cache_valid(cache_key):
            return self._cache[cache_key]
        
        upcoming = {}
        current_date = datetime.now()
        future_date = current_date + timedelta(days=days_ahead)
        
        for category, events in self.events.items():
            category_upcoming = []
            for event in events:
                event_date = self.parse_event_date(event.get('time', ''))
                
                if event_date and current_date <= event_date <= future_date:
                    category_upcoming.append(event)
            
            if category_upcoming:
                upcoming[category] = sorted(
                    category_upcoming,
                    key=lambda e: self.parse_event_date(e.get('time', '')) or datetime.max
                )
        
        # Кэшируем результат
        self._cache[cache_key] = upcoming
        self._cache["cache_time"][cache_key] = datetime.now()
        
        return upcoming
    
    def get_events_by_place(self, place_keyword: str) -> Dict[str, List[Dict]]:
        """Получить события по месту проведения"""
        results = {}
        place_lower = place_keyword.lower()
        
        for category, events in self.events.items():
            matching_events = [
                e for e in events 
                if place_lower in e.get('place', '').lower()
            ]
            if matching_events:
                results[category] = matching_events
        
        return results
    
    def get_events_by_date_range(self, start_date: datetime, end_date: datetime) -> Dict[str, List[Dict]]:
        """Получить события в указанном диапазоне дат"""
        results = {}
        
        for category, events in self.events.items():
            matching_events = []
            for event in events:
                event_date = self.parse_event_date(event.get('time', ''))
                if event_date and start_date <= event_date <= end_date:
                    matching_events.append(event)
            
            if matching_events:
                results[category] = sorted(
                    matching_events,
                    key=lambda e: self.parse_event_date(e.get('time', '')) or datetime.max
                )
        
        return results
    
    def export_to_csv(self, output_file: str = "events_export.csv") -> bool:
        """Экспортировать события в CSV"""
        try:
            rows = []
            for category, events in self.events.items():
                for event in events:
                    rows.append({
                        'ID': event.get('id', ''),
                        'Название': event.get('title', ''),
                        'Дата': event.get('time', ''),
                        'Место': event.get('place', ''),
                        'Категория': self.categories.get(category, category),
                        'Описание': event.get('desc', ''),
                        'Источник': event.get('source', ''),
                        'Уверенность': event.get('confidence', 0),
                        'Telegram': event.get('telegram_url', '')
                    })
            
            if not rows:
                logger.warning("⚠️ Нет событий для экспорта")
                return False
            
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"✅ Экспортировано {len(rows)} событий в {output_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при экспорте в CSV: {e}")
            return False
    
    def validate_event_data(self, event: Dict) -> Tuple[bool, List[str]]:
        """Валидировать данные события и вернуть список ошибок"""
        errors = []
        
        # Проверяем обязательные поля
        if not event.get('id'):
            errors.append("Отсутствует ID")
        
        if not event.get('title'):
            errors.append("Отсутствует название события")
        elif len(event.get('title', '')) < 5:
            errors.append("Название события слишком короткое (минимум 5 символов)")
        
        if not event.get('time'):
            errors.append("Отсутствует время события")
        elif not self.parse_event_date(event.get('time', '')):
            errors.append("Некорректный формат времени")
        
        if not event.get('place'):
            errors.append("Отсутствует место проведения")
        
        if event.get('confidence', 1.0) < 0 or event.get('confidence', 1.0) > 1.0:
            errors.append("Уверенность должна быть от 0 до 1")
        
        return len(errors) == 0, errors
    
    def get_advanced_statistics(self) -> Dict:
        """Получить расширенную статистику"""
        stats = {
            "total_events": 0,
            "by_category": {},
            "by_month": {},
            "upcoming_7days": 0,
            "upcoming_30days": 0,
            "average_confidence": 0,
            "sources": {},
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        current_date = datetime.now()
        confidence_scores = []
        
        for category, events in self.events.items():
            stats["by_category"][category] = len(events)
            stats["total_events"] += len(events)
            
            for event in events:
                # Сбор статистики по датам
                event_date = self.parse_event_date(event.get('time', ''))
                if event_date:
                    month_key = event_date.strftime("%Y-%m")
                    stats["by_month"][month_key] = stats["by_month"].get(month_key, 0) + 1
                    
                    # Предстоящие события
                    days_diff = (event_date - current_date).days
                    if 0 <= days_diff <= 7:
                        stats["upcoming_7days"] += 1
                    if 0 <= days_diff <= 30:
                        stats["upcoming_30days"] += 1
                
                # Источники
                source = event.get('source', 'unknown')
                stats["sources"][source] = stats["sources"].get(source, 0) + 1
                
                # Уверенность
                confidence = float(event.get('confidence', 0.5))
                confidence_scores.append(confidence)
                if confidence >= 0.8:
                    stats["confidence_distribution"]["high"] += 1
                elif confidence >= 0.5:
                    stats["confidence_distribution"]["medium"] += 1
                else:
                    stats["confidence_distribution"]["low"] += 1
        
        if confidence_scores:
            stats["average_confidence"] = round(sum(confidence_scores) / len(confidence_scores), 2)
        
        return stats
    
    def _check_cache_valid(self, cache_key: str) -> bool:
        """Проверить, валидные ли кэш данные"""
        if cache_key not in self._cache["cache_time"]:
            return False
        
        cache_age = (datetime.now() - self._cache["cache_time"][cache_key]).total_seconds()
        return cache_age < self.cache_ttl
    
    def clear_cache(self) -> None:
        """Очистить кэш"""
        self._cache = {
            "all_events": None,
            "search_results": {},
            "upcoming_events": None,
            "cache_time": {}
        }
        logger.info("✅ Кэш очищен")
    
    def print_statistics(self):
        """Вывести расширённую статистику"""
        stats = self.get_advanced_statistics()
        
        print("\n" + "="*70)
        print("📊 РАСШИРЁННАЯ СТАТИСТИКА МЕРОПРИЯТИЙ")
        print("="*70)
        
        # Основные числа
        print(f"\n🎯 Всего мероприятий: {stats['total_events']}")
        print(f"📈 Среднее качество данных: {stats['average_confidence']*100:.1f}%")
        
        # По категориям
        print("\n📂 По категориям:")
        for category, count in stats['by_category'].items():
            if count > 0:
                cat_name = self.categories.get(category, category)
                print(f"  {cat_name}: {count}")
        
        # Предстоящие события
        print(f"\n📅 Предстоящие события:")
        print(f"  На 7 дней: {stats['upcoming_7days']}")
        print(f"  На 30 дней: {stats['upcoming_30days']}")
        
        # Распределение по уверенности
        print(f"\n🎚️ Уверенность в данных:")
        print(f"  Высокая (≥80%): {stats['confidence_distribution']['high']}")
        print(f"  Средняя (50-80%): {stats['confidence_distribution']['medium']}")
        print(f"  Низкая (<50%): {stats['confidence_distribution']['low']}")
        
        # По месяцам
        if stats['by_month']:
            print(f"\n📆 По месяцам:")
            for month in sorted(stats['by_month'].keys()):
                count = stats['by_month'][month]
                print(f"  {month}: {count}")
        
        # Источники данных
        if stats['sources']:
            print(f"\n📡 Источники данных:")
            for source, count in sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {source}: {count}")
        
        print("\n" + "="*70 + "\n")
    
    def add_sample_events(self):
        """Добавить примеры мероприятий для демонстрации"""
        # Примечание: только реально спарсенные мероприятия добавляются сюда
        sample_events = {}
        
        # В данном методе хранятся только реально спарсенные мероприятия
        # Они добавляются автоматически из различных источников
        
        return self.save_events()


def main():
    """Основная функция для запуска парсера"""
    print("\n🎪 ПАРСЕР МЕРОПРИЯТИЙ МосПолитеха")
    print("="*50)
    
    parser = EventsParser()
    
    # Загружаем существующие события
    parser.load_events()
    
    # Выводим текущую статистику
    parser.print_statistics()
    
    # Удаляем старые события (более 30 дней назад)
    print("🧹 Удаляем старые мероприятия (более 30 дней назад)...")
    removed = parser.remove_old_events(days=30)
    print(f"✅ Удалено {removed} старых мероприятий")
    
    # Очищаем дубликаты и неполные записи
    print("🧹 Очищаем дубликаты и неполные записи...")
    cleaned = parser.clean_events()
    if cleaned > 0:
        print(f"✅ Очищено {cleaned} некорректных мероприятий")
    
    # Добавляем примеры новых событий
    print("📝 Добавляем примеры новых мероприятий...")
    if parser.add_sample_events():
        print("✅ Примеры событий добавлены успешно!")
    
    # Выводим обновленную статистику
    parser.print_statistics()
    
    print("🎯 Парсер завершил работу!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
