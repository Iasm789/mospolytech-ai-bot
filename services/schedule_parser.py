"""
Парсер расписания с сайта https://rasp.dmami.ru/
Использует API эндпоинт /site/group
"""

from typing import Dict, List, Optional, Set, Tuple
import logging
import requests
import json
import os
import csv
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


# Месяцы русского календаря
MONTHS_RU = {
    'янв': 1, 'января': 1,
    'фев': 2, 'февраля': 2,
    'мар': 3, 'марта': 3,
    'апр': 4, 'апреля': 4,
    'май': 5, 'мая': 5,
    'июн': 6, 'июня': 6,
    'июл': 7, 'июля': 7,
    'авг': 8, 'августа': 8,
    'сен': 9, 'сентября': 9,
    'окт': 10, 'октября': 10,
    'ноя': 11, 'ноября': 11,
    'дек': 12, 'декабря': 12,
}


class ScheduleParser:
    """Парсер расписания МосПолитеха"""
    
    BASE_URL = "https://rasp.dmami.ru"
    API_ENDPOINT = "/site/group"
    
    DAYS_OF_WEEK = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
        7: "Воскресенье",
    }
    
    LESSON_TIMES = {
        0: {"number": "1-я", "start": "08:30", "end": "10:00", "period": "morning"},
        1: {"number": "2-я", "start": "10:30", "end": "12:00", "period": "morning"},
        2: {"number": "3-я", "start": "12:30", "end": "14:00", "period": "afternoon"},
        3: {"number": "4-я", "start": "14:30", "end": "16:00", "period": "afternoon"},
        4: {"number": "5-я", "start": "16:30", "end": "18:00", "period": "afternoon"},
        5: {"number": "6-я", "start": "18:30", "end": "20:00", "period": "evening"},
        6: {"number": "7-я", "start": "20:30", "end": "22:00", "period": "evening"},
    }
    
    def __init__(self):
        """Инициализация парсера"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'{self.BASE_URL}/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self._all_groups = None
        self._load_groups()
    
    def _load_groups(self):
        """Загрузить список групп из CSV или через кеш"""
        try:
            # Сначала пытаемся загрузить из CSV (если существует)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, '..', 'data', 'num_group.csv')
            
            self._all_groups = set()
            
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            group = row[0].strip()
                            if group:
                                self._all_groups.add(group)
                
                logger.info(f"✅ Загружено {len(self._all_groups)} групп из CSV")
            else:
                logger.warning(f"⚠️ Файл CSV не найден: {csv_path}")
                logger.info("💡 Совет: Парсер будет проверять группы через API (медленнее, но работает)")
                self._all_groups = None  # Будет проверять через API в is_group_valid()
        except Exception as e:
            logger.error(f"⚠️ Ошибка при загрузке групп из CSV: {e}")
            logger.info("💡 Парсер переходит на режим проверки через API")
            self._all_groups = None
    
    def is_group_valid(self, group_number: str) -> bool:
        """
        Проверить наличие группы в списке
        Если CSV не загружен, пытается получить расписание через API
        """
        # Если группы загружены из CSV, проверяем в памяти
        if self._all_groups is not None:
            return group_number.upper() in {g.upper() for g in self._all_groups}
        
        # Если CSV не загружен, проверяем через API
        logger.info(f"🔍 Проверка группы {group_number} через API...")
        try:
            schedule = self.get_schedule_by_group(group_number)
            if schedule and schedule.get('days'):
                logger.info(f"✅ Группа {group_number} валидна")
                return True
            else:
                logger.warning(f"❌ Группа {group_number} не найдена на сервере")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке группы: {e}")
            return False
    
    def get_all_groups(self) -> Set[str]:
        """
        Получить все доступные группы
        Если CSV не загружен, возвращает пустое множество (API не предоставляет полный список)
        """
        if self._all_groups is None:
            logger.warning("⚠️ Список групп не загружен (CSV недоступен и API не предоставляет полный список)")
            return set()
        return self._all_groups
    
    @staticmethod
    def _extract_webinar_url(lesson: Dict) -> Optional[str]:
        """
        Извлечь ссылку на вебинар из данных занятия
        
        Args:
            lesson: Исходные данные занятия из API
            
        Returns:
            URL вебинара или None
        """
        try:
            auditories = lesson.get('auditories', [])
            if not auditories:
                return None
            
            for auditory in auditories:
                title = auditory.get('title', '')
                if 'href' in title:
                    match = re.search(r'href="([^"]+)"', title)
                    if match:
                        return match.group(1)
            
            return None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при извлечении ссылки вебинара: {e}")
            return None
    
    def close(self):
        """Закрытие сессии"""
        if self.session:
            self.session.close()
            logger.info("🛑 Сессия закрыта")
    
    @staticmethod
    def _parse_date_range(period_str: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Парсинг диапазона дат из строки "09 Фев - 11 Апр"
        
        Returns:
            Кортеж (дата_начала, дата_конца) или None
        """
        if not period_str or isinstance(period_str, str) and period_str.lower() in ['', 'n/a', 'none']:
            return None
        
        try:
            # Парсим строку вида "09 Фев - 11 Апр"
            parts = period_str.split('-')
            if len(parts) != 2:
                return None
            
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            
            # Парсим начальную дату
            start_match = re.match(r'(\d{1,2})\s+(\w+)', start_str)
            if not start_match:
                return None
            
            start_day = int(start_match.group(1))
            start_month_str = start_match.group(2).lower()
            
            # Парсим конечную дату
            end_match = re.match(r'(\d{1,2})\s+(\w+)', end_str)
            if not end_match:
                return None
            
            end_day = int(end_match.group(1))
            end_month_str = end_match.group(2).lower()
            
            # Преобразуем месяцы
            start_month = MONTHS_RU.get(start_month_str)
            end_month = MONTHS_RU.get(end_month_str)
            
            if not start_month or not end_month:
                return None
            
            # Текущий год (или предыдущий если уже прошли)
            current_year = datetime.now().year
            
            # Если конец года меньше начала, то конец в следующем году
            if end_month < start_month:
                end_year = current_year + 1
            else:
                end_year = current_year
            
            start_date = datetime(current_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
            
            return (start_date, end_date)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при парсинге даты '{period_str}': {e}")
            return None
    
    @staticmethod
    def _is_date_in_range(check_date: datetime, date_range: Optional[Tuple[datetime, datetime]]) -> bool:
        """
        Проверить входит ли дата в диапазон
        Если диапазон не указан, возвращает True
        """
        if not date_range:
            return True
        
        start_date, end_date = date_range
        return start_date.date() <= check_date.date() <= end_date.date()
    
    def filter_lessons_by_date(self, lessons: List[Dict], check_date: datetime = None) -> List[Dict]:
        """
        Отфильтровать занятия по дате
        
        Args:
            lessons: Список занятий
            check_date: Дата для проверки (по умолчанию сегодня)
        
        Returns:
            Отфильтрованный список занятий
        """
        if check_date is None:
            check_date = datetime.now()
        
        filtered = []
        for lesson in lessons:
            period = lesson.get('period', '')
            date_range = self._parse_date_range(period)
            
            if self._is_date_in_range(check_date, date_range):
                filtered.append(lesson)
        
        return filtered
    
    def get_week_number_by_date(self, check_date: datetime = None) -> int:
        """Получить номер дня недели (1-7)"""
        if check_date is None:
            check_date = datetime.now()
        return check_date.isoweekday()
    
    def get_schedule_by_group(self, group_number: str, session_mode: bool = False) -> Optional[Dict]:
        """
        Получить расписание по номеру группы
        
        Args:
            group_number: Номер группы (например, '231-3310')
            session_mode: Режим сессии (экзамены/зачёты)
            
        Returns:
            Словарь с расписанием или None
        """
        try:
            logger.info(f"🔍 Получение расписания для группы {group_number}...")
            
            # Устанавливаем cookie с номером группы
            self.session.cookies.set('group', group_number)
            
            params = {
                'group': group_number,
                'session': 1 if session_mode else 0
            }
            
            # Запрашиваем расписание через API
            url = f"{self.BASE_URL}{self.API_ENDPOINT}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.warning(f"⚠️ Сервер вернул статус: {data.get('status')}")
                return None
            
            # Парсим расписание
            schedule = self._parse_schedule_data(data, group_number)
            
            logger.info(f"✅ Расписание получено для группы {group_number}")
            
            return schedule
        
        except Exception as e:
            logger.error(f"❌ Ошибка при получении расписания: {e}", exc_info=True)
            return None
    
    def _parse_schedule_data(self, data: Dict, group_number: str) -> Dict:
        """
        Парсинг данных расписания из API ответа
        
        Args:
            data: JSON ответ от API
            group_number: Номер группы
            
        Returns:
            Структурированное расписание
        """
        schedule = {
            'group': group_number,
            'group_info': data.get('group', {}),
            'days': {},
            'all_lessons': []
        }
        
        grid = data.get('grid', {})
        
        # Парсим каждый день
        for day_key, day_schedule in grid.items():
            day_num = int(day_key)
            day_name = self.DAYS_OF_WEEK.get(day_num, f"День {day_num}")
            
            day_data = {
                'day_num': day_num,
                'day_name': day_name,
                'lessons': []
            }
            
            # Парсим каждое время занятия
            for time_key, lessons in day_schedule.items():
                time_num = int(time_key)
                time_info = self.LESSON_TIMES.get(time_num, {
                    "number": f"Пара {time_num}",
                    "start": "??:??",
                    "end": "??:??",
                    "period": "unknown"
                })
                
                if not lessons:
                    continue
                
                # Парсим каждый предмет
                for lesson in lessons:
                    parsed_lesson = {
                        'subject': lesson.get('sbj', 'N/A'),
                        'type': lesson.get('type', 'N/A'),
                        'teacher': lesson.get('teacher', ''),
                        'teachers': lesson.get('teachers', []),
                        'classrooms': lesson.get('shortRooms', []),
                        'location': lesson.get('location', ''),
                        'period': lesson.get('dts', ''),
                        'date_from': lesson.get('df', ''),
                        'date_to': lesson.get('dt', ''),
                        'time_slot': time_num,
                        'lesson_number': time_info.get('number', f'Пара {time_num}'),
                        'time_start': time_info.get('start', '??:??'),
                        'time_end': time_info.get('end', '??:??'),
                        'time_str': f"{time_info.get('start', '??:??')} - {time_info.get('end', '??:??')}",
                        'time_period': time_info.get('period', 'unknown'),
                        'day_num': day_num,
                        'webinar_url': self._extract_webinar_url(lesson),
                        'raw': lesson
                    }
                    
                    day_data['lessons'].append(parsed_lesson)
                    schedule['all_lessons'].append(parsed_lesson)
            
            if day_data['lessons']:  # Добавляем только дни с занятиями
                schedule['days'][day_name] = day_data
        
        return schedule
    
    def get_schedule_by_group_pretty(self, group_number: str) -> str:
        """
        Получить расписание в красивом текстовом формате (консоль)
        
        Args:
            group_number: Номер группы
            
        Returns:
            Форматированная строка расписания
        """
        schedule = self.get_schedule_by_group(group_number)
        
        if not schedule:
            return f"❌ Не удалось получить расписание для группы {group_number}"
        
        result = []
        result.append(f"\n📅 Расписание группы: {group_number}")
        result.append(f"   Курс: {schedule['group_info'].get('course')}")
        result.append(f"   Период: {schedule['group_info'].get('dateFrom')} - {schedule['group_info'].get('dateTo')}")
        result.append("")
        
        for day_name, day_info in schedule['days'].items():
            result.append(f"\n📆 {day_name}")
            
            for lesson in day_info['lessons']:
                result.append(f"   ⏰ {lesson['time_str']} ({lesson['type']})")
                result.append(f"      📚 {lesson['subject']}")
                if lesson['classrooms']:
                    result.append(f"      🏫 Аудитория: {', '.join(lesson['classrooms'])}")
                if lesson['teacher']:
                    result.append(f"      👨‍🏫 {lesson['teacher'][:60]}...")
                if lesson['period']:
                    result.append(f"      📋 {lesson['period']}")
                if lesson.get('webinar_url'):
                    result.append(f"      🌐 Вебинар: {lesson['webinar_url']}")
            
        return "\n".join(result)


# Создаём глобальный экземпляр парсера
parser = ScheduleParser()

