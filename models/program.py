"""
Модель данных для программ обучения
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Faculty(BaseModel):
    """Модель факультета"""
    id: str
    name: str
    code: str
    description: Optional[str] = None
    url: Optional[str] = None


class Program(BaseModel):
    """Модель программы обучения"""
    id: str
    title: str
    faculty_id: str
    faculty_name: str
    code: str  # Код программы (например, 09.03.01)
    direction: str  # Направление подготовки
    form: str  # Очная/Очно-заочная/Заочная
    level: str  = "Бакалавриат"  # Уровень обучения
    
    # Кратко информация
    description: Optional[str] = None
    brief_info: Optional[str] = None
    
    # Подробная информация
    goal: Optional[str] = None  # Цель программы
    profile: Optional[str] = None  # Профиль программы
    specialization: Optional[str] = None  # Специализация
    
    # Условия поступления
    disciplines: List[str] = []  # Дисциплины ЕГЭ
    min_score: Optional[int] = None  # Минимальный балл
    places: Optional[str] = None  # Количество мест
    
    # Карьера
    career_prospects: Optional[str] = None
    professions: List[str] = []  # Возможные профессии
    
    # Дополнительная информация
    duration: Optional[str] = None  # Длительность (в годах)
    credits: Optional[str] = None  # Кредиты
    subjects: List[str] = []  # Основные предметы
    
    # Источники
    url: str  # Ссылка на страницу программы
    timestamp: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ProgramsData(BaseModel):
    """Полный набор данных о программах"""
    faculties: List[Faculty]
    programs: List[Program]
    last_updated: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
