"""
Модель данных для студенческих проектов
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Project(BaseModel):
    """Модель студенческого проекта"""
    id: str
    title: str
    category: str  # Основная категория (ЦПД, Дизайн-мышление и т.д.)
    theme: Optional[str] = None  # Тематика проекта (IT, Дизайн, Мультимедиа и т.д.)
    description: str
    relevance: Optional[str] = None
    problem: Optional[str] = None
    goal: Optional[str] = None
    tasks: List[str] = []
    result: Optional[str] = None
    partners: Optional[List[str]] = None
    url: str
    image_url: Optional[str] = None
    timestamp: datetime = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ProjectCategory(BaseModel):
    """Категория проектов"""
    name: str
    url: str
    description: Optional[str] = None


class ProjectsData(BaseModel):
    """Полный набор данных о проектах"""
    categories: List[ProjectCategory]
    projects: List[Project]
    last_updated: datetime = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
