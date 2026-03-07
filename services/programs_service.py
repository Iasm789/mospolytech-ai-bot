"""
Сервис для управления программами обучения
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio

from models.program import Program, ProgramsData, Faculty
from services.programs_parser import parser
from utils.logger import logger


class ProgramsService:
    """Сервис для работы с программами обучения"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.programs_data: Optional[ProgramsData] = None
        self.programs_by_faculty: Dict[str, List[Program]] = {}
        self.last_update_time = None
        self.cache_duration = timedelta(hours=24)  # Кэш на 24 часа
    
    async def init_programs(self, force_refresh: bool = False) -> bool:
        """
        Инициализация данных программ
        
        Args:
            force_refresh: Принудительно обновить данные
            
        Returns:
            True если успешно, False иначе
        """
        try:
            # Проверяем, нужно ли обновить
            if not force_refresh and self.programs_data:
                if self.last_update_time and datetime.now() - self.last_update_time < self.cache_duration:
                    logger.info("📚 Программы уже загружены в памяти")
                    return True
            
            # Пытаемся загрузить кэш
            logger.info("📚 Загрузка программ из кэша...")
            self.programs_data = parser.load_cache()
            
            # Если кэш есть, применяем и используем его
            if self.programs_data:
                self._organize_programs()
                self.last_update_time = datetime.now()
                logger.info(f"✅ Кэш загружен: {len(self.programs_data.programs)} программ, {len(self.programs_data.faculties)} факультетов")
                return True
            
            # Если кэша нет, парсим заново
            logger.info("🔄 Парсинг программ с сайта...")
            async with parser as p:
                self.programs_data = await p.parse_all_programs()
            
            # Сохраняем в кэш
            if self.programs_data and len(self.programs_data.programs) > 0:
                await asyncio.to_thread(parser.save_cache, self.programs_data)
                self._organize_programs()
                self.last_update_time = datetime.now()
                logger.info(f"✅ Программы обновлены: {len(self.programs_data.programs)} программ")
                return True
            else:
                logger.warning("❌ Парсинг вернул 0 программ")
                self.programs_data = ProgramsData(faculties=[], programs=[], last_updated=datetime.now())
                self.last_update_time = datetime.now()
                return False
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации программ: {e}")
            # Пытаемся использовать кэш даже если произошла ошибка
            self.programs_data = parser.load_cache()
            if self.programs_data:
                self._organize_programs()
                self.last_update_time = datetime.now()
                return True
            return False
    
    def _organize_programs(self):
        """Организовать программы по факультетам"""
        if not self.programs_data:
            return
        
        self.programs_by_faculty = {}
        
        for faculty in self.programs_data.faculties:
            programs = [p for p in self.programs_data.programs if p.faculty_id == faculty.id]
            if programs:
                self.programs_by_faculty[faculty.id] = programs
    
    def get_faculties(self) -> List[Faculty]:
        """Получить список всех факультетов"""
        if not self.programs_data:
            return []
        return self.programs_data.faculties
    
    def get_all_programs(self) -> List[Program]:
        """Получить список всех программ"""
        if not self.programs_data:
            return []
        return self.programs_data.programs
    
    def get_programs_by_faculty(self, faculty_id: str) -> List[Program]:
        """Получить программы конкретного факультета"""
        return self.programs_by_faculty.get(faculty_id, [])
    
    def get_program_by_id(self, program_id: str) -> Optional[Program]:
        """Получить программу по ID"""
        if not self.programs_data:
            return None
        for program in self.programs_data.programs:
            if program.id == program_id:
                return program
        return None
    
    def get_faculty_by_id(self, faculty_id: str) -> Optional[Faculty]:
        """Получить факультет по ID"""
        if not self.programs_data:
            return None
        for faculty in self.programs_data.faculties:
            if faculty.id == faculty_id:
                return faculty
        return None
    
    def search_programs(self, query: str) -> List[Program]:
        """Поиск программ по названию или описанию"""
        if not self.programs_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for program in self.programs_data.programs:
            if (query_lower in program.title.lower() or
                query_lower in program.direction.lower() or
                (program.description and query_lower in program.description.lower())):
                results.append(program)
        
        return results
    
    def get_faculty_name(self, faculty_id: str) -> str:
        """Получить название факультета"""
        faculty = self.get_faculty_by_id(faculty_id)
        return faculty.name if faculty else "Неизвестный факультет"


# Создаем глобальный экземпляр сервиса
programs_service = ProgramsService()


# Функция для инициализации сервиса при запуске приложения
async def init_programs_data():
    """Инициализировать данные программ при запуске"""
    success = await programs_service.init_programs()
    if success:
        logger.info(f"✅ Программы успешно загружены при старте")
    else:
        logger.warning("⚠️ Ошибка загрузки программ при старте")
    return success
