"""
Сервис для управления студенческими проектами
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio

from models.project import Project, ProjectsData
from services.projects_parser import parser
from utils.logger import logger


class ProjectsService:
    """Сервис для работы с проектами"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.projects_data: Optional[ProjectsData] = None
        self.projects_by_category: Dict[str, List[Project]] = {}
        self.all_tags: set = set()
        self.last_update_time = None
        self.cache_duration = timedelta(hours=6)  # Кэш на 6 часов
    
    async def init_projects(self, force_refresh: bool = False) -> bool:
        """
        Инициализация данных проектов
        
        Args:
            force_refresh: Принудительно обновить данные
            
        Returns:
            True если успешно, False иначе
        """
        try:
            # Проверяем, нужно ли обновить
            if not force_refresh and self.projects_data:
                if self.last_update_time and datetime.now() - self.last_update_time < self.cache_duration:
                    logger.info("📦 Проекты уже загружены в памяти")
                    return True
            
            # Пытаемся загрузить кэш
            logger.info("📦 Загрузка проектов из кэша...")
            self.projects_data = parser.load_cache()
            
            # Если кэш есть, применяем миграции и используем его
            if self.projects_data:
                self._migrate_projects_data()  # Обновляем структуру если нужно
                self._organize_projects()
                self.last_update_time = datetime.now()
                logger.info(f"✅ Кэш загружен: {len(self.projects_data.projects)} проектов")
                return True
            
            # Если кэша нет, парсим заново (но это редко работает для Tilda)
            logger.info("🔄 Парсинг проектов с сайта...")
            async with parser as p:
                self.projects_data = await p.parse_all_projects()
            
            # Сохраняем в кэш только если парсинг был успешным
            if self.projects_data and len(self.projects_data.projects) > 0:
                await parser.save_cache(self.projects_data)
                self._organize_projects()
                self.last_update_time = datetime.now()
                logger.info(f"✅ Проекты обновлены: {len(self.projects_data.projects)} проектов")
                return True
            else:
                logger.warning("❌ Парсинг вернул 0 проектов, используем пустые данные")
                # Создаем пустой объект данных, но не перезаписываем кэш
                self.projects_data = ProjectsData(categories=[], projects=[], last_updated=datetime.now())
                self.last_update_time = datetime.now()
                return False
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации проектов: {e}")
            # Пытаемся использовать кэш даже если произошла ошибка
            self.projects_data = parser.load_cache()
            if self.projects_data:
                self._migrate_projects_data()
                self._organize_projects()
                return True
            return False
    
    def _migrate_projects_data(self):
        """Миграция: добавление поля theme к проектам которые его не имеют"""
        if not self.projects_data:
            return
        
        from services.projects_parser import ProjectsParser
        
        # Инициализируем парсер для использования функции определения тематики
        parser_instance = ProjectsParser()
        
        for project in self.projects_data.projects:
            # Если у проекта нет тематики, определяем её из текста
            if not project.theme or project.theme == "":
                # Комбинируем все доступные текстовые поля
                combined_text = f"{project.title} {project.description} {project.goal or ''} {project.problem or ''}"
                project.theme = parser_instance._extract_theme_from_text(combined_text)
                logger.info(f"🔄 Добавлена тематика -> {project.title}: {project.theme}")

    
    def _organize_projects(self):
        """Организация проектов по тематикам"""
        if not self.projects_data:
            return
        
        self.projects_by_category = {}
        self.all_tags = set()
        
        for project in self.projects_data.projects:
            # Группировка по тематикам (theme вместо category)
            theme = project.theme or "Другое"
            if theme not in self.projects_by_category:
                self.projects_by_category[theme] = []
            self.projects_by_category[theme].append(project)
            
            # Сбор всех тематик
            if theme:
                self.all_tags.add(theme)
    
    def get_all_categories(self) -> List[str]:
        """
        Получение списка всех тематик проектов
        
        Returns:
            Список уникальных тематик
        """
        return sorted(list(self.all_tags))
    
    def get_projects_by_category(self, category: str) -> List[Project]:
        """
        Получение проектов по тематике
        
        Args:
            category: Название тематики
            
        Returns:
            Список проектов
        """
        return self.projects_by_category.get(category, [])
    
    def get_all_projects(self, limit: Optional[int] = None) -> List[Project]:
        """
        Получение всех проектов
        
        Args:
            limit: Количество проектов
            
        Returns:
            Список проектов
        """
        if not self.projects_data:
            return []
        
        projects = self.projects_data.projects
        if limit:
            return projects[:limit]
        return projects
    
    def search_projects(self, query: str) -> List[Project]:
        """
        Поиск проектов по названию или описанию
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных проектов
        """
        if not self.projects_data:
            return []
        
        query_lower = query.lower()
        results = []
        
        for project in self.projects_data.projects:
            if (query_lower in project.title.lower() or 
                query_lower in project.description.lower() or
                (project.goal and query_lower in project.goal.lower())):
                results.append(project)
        
        return results
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """
        Получение проекта по ID
        
        Args:
            project_id: ID проекта
            
        Returns:
            Объект Project или None
        """
        if not self.projects_data:
            return None
        
        for project in self.projects_data.projects:
            if project.id == project_id:
                return project
        
        return None
    
    def get_projects_summary(self) -> Dict[str, any]:
        """
        Получение сводки по проектам
        
        Returns:
            Статистика проектов
        """
        if not self.projects_data:
            return {
                "total": 0,
                "by_category": {},
                "last_updated": None
            }
        
        summary = {
            "total": len(self.projects_data.projects),
            "by_category": {},
            "last_updated": self.projects_data.last_updated
        }
        
        for category, projects in self.projects_by_category.items():
            summary["by_category"][category] = len(projects)
        
        return summary
    
    def get_trending_projects(self, limit: int = 5) -> List[Project]:
        """
        Получение "популярных" проектов (последних добавленных)
        
        Args:
            limit: Количество проектов
            
        Returns:
            Список проектов
        """
        if not self.projects_data:
            return []
        
        sorted_projects = sorted(
            self.projects_data.projects,
            key=lambda p: p.timestamp or datetime.min,
            reverse=True
        )
        
        return sorted_projects[:limit]
    
    def format_project_short(self, project: Project) -> str:
        """
        Форматирование информации о проекте (краткий вид)
        
        Args:
            project: Объект Project
            
        Returns:
            Отформатированный текст
        """
        text = f"📌 {project.title}\n"
        text += f"📂 Категория: {project.category}\n"
        if project.goal:
            text += f"🎯 Цель: {project.goal[:100]}...\n"
        text += f"🔗 <a href='{project.url}'>Подробнее на сайте</a>\n"
        return text
    
    def format_project_detailed(self, project: Project) -> str:
        """
        Форматирование информации о проекте (полный вид)
        
        Args:
            project: Объект Project
            
        Returns:
            Отформатированный текст
        """
        text = f"📌 <b>{project.title}</b>\n"
        text += f"📂 Категория: {project.category}\n\n"
        
        if project.relevance:
            text += f"<b>🌟 Актуальность:</b>\n{project.relevance[:500]}\n\n"
        
        if project.goal:
            text += f"<b>🎯 Цель:</b>\n{project.goal[:500]}\n\n"
        
        if project.problem:
            text += f"<b>⚠️ Проблема:</b>\n{project.problem[:500]}\n\n"
        
        if project.tasks:
            text += "<b>✅ Задачи:</b>\n"
            for i, task in enumerate(project.tasks[:5], 1):
                text += f"{i}. {task[:100]}\n"
            text += "\n"
        
        if project.result:
            text += f"<b>🏆 Результат:</b>\n{project.result[:500]}\n\n"
        
        text += f"<a href='{project.url}'>🔗 Перейти на сайт проекта</a>"
        
        return text


# Глобальный сервис проектов
projects_service = ProjectsService()
