"""
Парсер для сайта проектов https://projects.mospolytech.ru/
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from datetime import datetime
import json
import re
from pathlib import Path
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except:
    SELENIUM_AVAILABLE = False

from models.project import Project, ProjectCategory, ProjectsData
from utils.logger import logger


class ProjectsParser:
    """Парсер проектов с сайта https://projects.mospolytech.ru/"""
    
    BASE_URL = "https://projects.mospolytech.ru"
    
    # Основные категории проектов на сайте
    CATEGORIES = {
        "cpd_mospolytech": {
            "name": "ЦПД - Витрина проектов",
            "url": "https://projects.mospolytech.ru/cpd_mospolytech",
            "description": "Проекты Московского политехнического университета в рамках дисциплины «Проектная деятельность»"
        },
        "design-thinking": {
            "name": "Дизайн-мышление",
            "url": "https://projects.mospolytech.ru/design-thinking",
            "description": "Проекты дизайн-мышления"
        },
        "upkcpd": {
            "name": "Учебно-производственный комплекс",
            "url": "https://projects.mospolytech.ru/upkcpd",
            "description": "Проекты учебно-производственного комплекса"
        },
        "accelerator": {
            "name": "Акселерационная программа",
            "url": "https://projects.mospolytech.ru/accelerator",
            "description": "Проекты акселерационной программы"
        },
        "dpo": {
            "name": "Программа ДПО",
            "url": "https://projects.mospolytech.ru/dpo",
            "description": "Проекты программы ДПО"
        }
    }
    
    # Возможные тематики проектов (извлекаются из текста)
    PROJECT_THEMES = {
        "IT": ["IT", "ИТ", "компьютер", "программ", "софтвер", "код", "разработк", "алгоритм", "данн", "базаданн", "приложен", "интернет"],
        "Дизайн": ["дизайн", "графи", "визуал", "интерфейс", "UI", "UX", "веб-диз", "иллюстр"],
        "Мультимедиа": ["видео", "кино", "фото", "медиа", "аудио", "звук", "монтаж", "кадр", "фильм"],
        "Научные проекты": ["исследован", "наука", "научн", "эксперимент", "гипотез", "тестирован", "анализ"],
        "Проекты технологического лидерства": ["технолог", "лидер", "инновац", "разработк", "передов", "авангард"],
        "Соцтех": ["соцсет", "социаль", "общество", "волонтер", "благотворител", "помощь", "ком мунит"],
        "Стратегические проекты вуза": ["стратег", "университ", "вуз", "образ", "мосполитех"],
        "Технология": ["техн", "механик", "машин", "устройств", "систем", "процес", "мотор", "двигател"],
        "Транспорт": ["автомоб", "авто", "машин", "транспорт", "дорож", "движен", "автобус", "авиа"],
        "Урбанистика": ["город", "урбан", "архитект", "планиров", "простран", "инфраструктур"],
        "Химбиотех": ["химиче", "биотех", "фарма", "молекул", "синтез", "реакц", "вещество"],
    }
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Инициализация парсера
        
        Args:
            cache_dir: Директория для кэширования данных
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "projects_cache.json"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Контекстный менеджер для асинхронной сессии"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """
        Получение содержимого URL
        
        Args:
            url: URL для загрузки
            
        Returns:
            HTML содержимое или None
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30), headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Ошибка при загрузке {url}: статус {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout при загрузке {url}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {e}")
            return None
    
    def fetch_url_with_selenium(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Получение содержимого URL с использованием Selenium (для JS-контента)
        
        Args:
            url: URL для загрузки
            max_retries: Максимальное количество попыток
            
        Returns:
            HTML содержимое или None
        """
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium не установлен, используем обычный fetch")
            return None
        
        for attempt in range(max_retries):
            driver = None
            try:
                options = Options()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                options.add_argument('--blink-settings=imagesEnabled=false')  # Отключаем изображения для ускорения
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                
                logger.info(f"  ⏳ Открываем {url} через Chrome WebDriver...")
                driver.get(url)
                
                # Ждем загрузки содержимого (максимум 15 секунд)
                logger.info(f"  ⏳ Ождаем загрузки JavaScript...")
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[href*='tproduct']")) > 0
                    )
                    logger.info(f"  ✅ Найдены элементы с tproduct")
                except:
                    logger.info(f"  ℹ️  Timeout ожидания tproduct, берем то что есть...")
                
                # Даем дополнительное время на рендеринг
                time.sleep(2)
                
                html = driver.page_source
                driver.quit()
                
                logger.info(f"  ✅ Успешно загружено {len(html)} символов HTML")
                return html
                
            except Exception as e:
                logger.warning(f"  ⚠️  Ошибка Selenium при загрузке {url} (попытка {attempt + 1}/{max_retries}): {e}")
                try:
                    if driver:
                        driver.quit()
                except:
                    pass
                
                if attempt < max_retries - 1:
                    time.sleep(2)  # Задержка перед повторной попыткой
        
        return None
    
    def _extract_theme_from_text(self, text: str) -> str:
        """
        Извлечение тематики проекта из текста
        
        Args:
            text: Текст для анализа
            
        Returns:
            Найденная тематика или 'Другое'
        """
        text_lower = text.lower()
        # Считаем совпадения ключевых слов для каждой тематики
        theme_scores = {}
        
        for theme, keywords in self.PROJECT_THEMES.items():
            score = 0
            for keyword in keywords:
                score += text_lower.count(keyword)
            if score > 0:
                theme_scores[theme] = score
        
        # Возвращаем тематику с наибольшим количеством совпадений
        if theme_scores:
            return max(theme_scores, key=theme_scores.get)
        
        return "Другое"
    
    async def parse_project_detail(self, url: str) -> Optional[Project]:
        """
        Парсинг детальной страницы проекта
        
        Args:
            url: URL страницы проекта
            
        Returns:
            Объект Project или None
        """
        try:
            html = await self.fetch_url(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлечение названия
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Неизвестный проект"
            
            # Получаем весь текст содержимого
            all_text = soup.get_text()
            
            # Извлечение тематики (ищём совпадения с ключевыми словами)
            theme = self._extract_theme_from_text(all_text)
            
            # Поиск изображения
            image_url = None
            img_elem = soup.find('img')
            if img_elem and img_elem.get('src'):
                image_url = img_elem['src']
                if not image_url.startswith('http'):
                    image_url = self.BASE_URL + image_url
            
            # Параллельное извлечение всех разделов
            relevance = self._extract_section(all_text, 'Актуальность', 'Проблема')
            problem = self._extract_section(all_text, 'Проблема', 'Цель')
            goal = self._extract_section(all_text, 'Цель', 'Задачи')
            tasks_text = self._extract_section(all_text, 'Задачи', 'Результат')
            result = self._extract_section(all_text, 'Результат', 'Партнёры')
            
            # Парсим задачи из текста (могут быть пронумерованы)
            tasks = self._parse_tasks(tasks_text) if tasks_text else []
            
            # Создание объекта Project
            project_id = url.split('/')[-1]
            
            # Подготовка описания из актуальности
            description = relevance[:200] + "..." if relevance and len(relevance) > 200 else relevance
            
            project = Project(
                id=project_id,
                title=title,
                category="",  # Будет заполнена при парсинге категории
                theme=theme,  # Тематика извлеченная из текста
                description=description or title,
                relevance=relevance,
                problem=problem,
                goal=goal,
                tasks=tasks[:10],  # Берём первые 10 задач
                result=result,
                url=url,
                image_url=image_url,
                timestamp=datetime.now()
            )
            
            return project
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге проекта {url}: {e}")
            return None
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> Optional[str]:
        """
        Извлечение текста между двумя маркерами
        
        Args:
            text: Полный текст
            start_marker: Начальный маркер
            end_marker: Конечный маркер
            
        Returns:
            Найденный текст или None
        """
        try:
            start_idx = text.find(start_marker)
            end_idx = text.find(end_marker)
            
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                result = text[start_idx + len(start_marker):end_idx].strip()
                return result if result else None
            return None
        except:
            return None
    
    def _parse_tasks(self, tasks_text: str) -> List[str]:
        """
        Парсинг списка задач из текста
        
        Args:
            tasks_text: Текст с задачами
            
        Returns:
            Список задач
        """
        if not tasks_text:
            return []
        
        tasks = []
        
        # Пробуем найти пронумерованные задачи (1., 2., 3., и т.д.)
        numbered_pattern = r'^\d+\.\s+(.+?)(?=^\d+\.|$)'
        matches = re.findall(numbered_pattern, tasks_text, re.MULTILINE | re.DOTALL)
        
        if matches:
            for match in matches:
                task = match.strip()
                # Берём первую строку задачи (до переноса)
                first_line = task.split('\n')[0].strip()
                if first_line and len(first_line) > 5:  # Минимальная длина для задачи
                    tasks.append(first_line)
        else:
            # Если нет нумерации, пробуем разбить по точкам или переносам
            for line in tasks_text.split('\n'):
                line = line.strip()
                if line and len(line) > 5 and not line.startswith('Результат'):
                    # Удаляем номеры в начале if they exist
                    line = re.sub(r'^\d+\.\s*', '', line)
                    if line:
                        tasks.append(line)
        
        return tasks[:10]  # Берём первые 10 задач
    
    def _get_pagination_urls(self, html: str, base_url: str) -> List[str]:
        """
        Получение URL всех страниц категории (для проверки и дублирования)
        Примечание: На сайте с Tilda обычно все проекты загружаются в один HTML после JS рендеринга
        
        Args:
            html: HTML содержимое главной страницы
            base_url: базовый URL категории
            
        Returns:
            Список URL для парсинга (обычно только базовый)
        """
        urls = [base_url]
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем ссылки на пагинацию в HTML
            pagination_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                # Проверяем есть ли в ссылке параметр пагинации (tfc_page)
                if 'tfc_page' in href:
                    full_url = base_url + href if href.startswith('?') else href
                    pagination_links.append(full_url)
            
            # Удаляем дубликаты и сортируем
            pagination_links = sorted(list(set(pagination_links)))
            
            if pagination_links:
                logger.info(f"ℹ️  Найдены ссылки пагинации: {len(pagination_links)} страниц")
                logger.info(f"    Замечание: Tilda обычно группирует показ через JS, проверим количество найденных проектов")
                urls.extend(pagination_links)
            
            return urls
        except Exception as e:
            logger.warning(f"⚠️  Ошибка при получении пагинации: {e}")
            return urls
    
    async def parse_category(self, category_url: str) -> List[Dict]:
        """
        Парсинг категории проектов со всех страниц (с поддержкой пагинации)
        
        Args:
            category_url: URL категории
            
        Returns:
            Список найденных проектов
        """
        try:
            logger.info(f"📁 Загрузка категории: {category_url}")
            
            # Сначала загружаем главную страницу с помощью Selenium (сайт требует JS рендеринга)
            logger.info(f"⏳ Используем Selenium для рендеринга JavaScript...")
            html = self.fetch_url_with_selenium(category_url)
            
            if not html:
                logger.warning(f"❌ Не удалось загрузить {category_url}")
                return []
            
            # Получаем все страницы пагинации
            page_urls = self._get_pagination_urls(html, category_url)
            logger.info(f"📄 Всего страниц для парсинга: {len(page_urls)}")
            
            all_projects = []
            
            # Парсим каждую страницу
            for page_idx, page_url in enumerate(page_urls):
                logger.info(f"📑 Загрузка страницы {page_idx + 1}/{len(page_urls)}")
                
                if page_idx == 0:
                    # Используем уже загруженный HTML для первой страницы
                    page_html = html
                else:
                    # Загружаем остальные страницы с Selenium (так как они тоже требуют JS)
                    logger.info(f"  ⏳ Загрузка страницы {page_idx + 1} с Selenium...")
                    page_html = self.fetch_url_with_selenium(page_url)
                    
                    if not page_html:
                        logger.warning(f"  ⚠️  Не удалось загрузить страницу {page_idx + 1}, пропускаем")
                        continue
                    
                    await asyncio.sleep(1)  # Увеличиваем задержку между страницами
                
                soup = BeautifulSoup(page_html, 'html.parser')
                project_links = []
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'tproduct' in href:
                        project_links.append(link)
                
                logger.info(f"  🔗 Найдено {len(project_links)} проектов на странице {page_idx + 1}")
                
                # Парсим все проекты на странице
                projects = await self._parse_links_to_projects(category_url, project_links)
                all_projects.extend(projects)
                
                # Задержка между страницами
                await asyncio.sleep(1)
            
            logger.info(f"🎉 Всего собрано проектов: {len(all_projects)}")
            return all_projects
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при парсинге категории {category_url}: {e}")
            return []
    
    async def _parse_links_to_projects(self, category_url: str, project_links: List) -> List[Dict]:
        """
        Парсинг найденных ссылок на проекты
        
        Args:
            category_url: URL категории (для логирования)
            project_links: Список elem BeautifulSoup с href
            
        Returns:
            Список словарей проектов
        """
        # Удаляем дубликаты и получаем уникальные URLs
        seen_urls = set()
        unique_project_urls = []
        
        for link in project_links:
            href = link.get('href', '')
            
            # Нормализуем URL
            if href.startswith('http'):
                full_url = href
            else:
                full_url = self.BASE_URL + href if href.startswith('/') else self.BASE_URL + '/' + href
            
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                unique_project_urls.append(full_url)
        
        logger.info(f"✅ Уникальных проектов: {len(unique_project_urls)}")
        
        # Парсим каждый проект (БЕЗ ограничения по количеству)
        projects = []
        
        for idx, project_url in enumerate(unique_project_urls):
            logger.info(f"    📄 Парсинг {idx + 1}/{len(unique_project_urls)}: {project_url}")
            
            try:
                project = await self.parse_project_detail(project_url)
                
                if project:
                    projects.append(project.dict())
                    logger.info(f"      ✅ Успешно: {project.title}")
                else:
                    logger.warning(f"      ⚠️  Не удалось спарсить проект")
                    
            except Exception as e:
                logger.warning(f"      ❌ Ошибка при парсинге: {e}")
            
            # Задержка между запросами
            await asyncio.sleep(0.3)
        
        logger.info(f"  🎉 Страница завершена: {len(projects)} проектов спарсено")
        return projects
    
    async def parse_all_projects(self) -> ProjectsData:
        """
        Парсинг всех проектов со всех категорий
        
        Returns:
            Объект ProjectsData со всеми проектами
        """
        try:
            logger.info("🚀 Начало парсинга всех проектов...")
            
            all_projects = []
            categories = []
            
            # Парсим каждую категорию
            for category_key, category_info in self.CATEGORIES.items():
                logger.info(f"Парсинг категории: {category_info['name']}")
                
                categories.append(ProjectCategory(
                    name=category_info['name'],
                    url=category_info['url'],
                    description=category_info['description']
                ))
                
                projects_data = await self.parse_category(category_info['url'])
                
                # Добавляем категорию к каждому проекту
                for project_dict in projects_data:
                    project_dict['category'] = category_info['name']
                    all_projects.append(project_dict)
                
                logger.info(f"✅ Категория '{category_info['name']}': {len(projects_data)} проектов")
                
                # Задержка между категориями
                await asyncio.sleep(1)
            
            # Преобразуем в объекты Project
            projects = [Project(**p) for p in all_projects]
            
            projects_data = ProjectsData(
                categories=categories,
                projects=projects,
                last_updated=datetime.now()
            )
            
            logger.info(f"✅ Парсинг завершен! Всего проектов: {len(projects)}")
            
            return projects_data
            
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге: {e}")
            return ProjectsData(categories=[], projects=[], last_updated=datetime.now())
    
    async def save_cache(self, data: ProjectsData) -> bool:
        """
        Сохранение данных в кэш
        
        Args:
            data: Данные для сохранения
            
        Returns:
            True если успешно, False иначе
        """
        try:
            # Конвертируем проекты в словари с правильной сериализацией datetime
            categories = [cat.dict() for cat in data.categories]
            projects = []
            for proj in data.projects:
                proj_dict = proj.dict()
                # Конвертируем timestamp в ISO format
                if proj_dict.get('timestamp') and isinstance(proj_dict['timestamp'], datetime):
                    proj_dict['timestamp'] = proj_dict['timestamp'].isoformat()
                projects.append(proj_dict)
            
            cache_data = {
                'categories': categories,
                'projects': projects,
                'last_updated': data.last_updated.isoformat() if data.last_updated else None
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Данные сохранены в кэш: {self.cache_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении кэша: {e}")
            return False
    
    def load_cache(self) -> Optional[ProjectsData]:
        """
        Загрузка данных из кэша
        
        Returns:
            Объект ProjectsData или None
        """
        try:
            if not self.cache_file.exists():
                logger.info("Файл кэша не найден")
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            categories = [ProjectCategory(**cat) for cat in cache_data.get('categories', [])]
            
            # Конвертируем проекты с правильной обработкой timestamp
            projects = []
            for proj_dict in cache_data.get('projects', []):
                # Если timestamp это строка, конвертируем обратно в datetime
                if proj_dict.get('timestamp') and isinstance(proj_dict['timestamp'], str):
                    try:
                        proj_dict['timestamp'] = datetime.fromisoformat(proj_dict['timestamp'])
                    except:
                        proj_dict['timestamp'] = datetime.now()
                projects.append(Project(**proj_dict))
            
            last_updated = cache_data.get('last_updated')
            if last_updated and isinstance(last_updated, str):
                try:
                    last_updated = datetime.fromisoformat(last_updated)
                except:
                    last_updated = None
            
            logger.info(f"✅ Кэш загружен: {len(projects)} проектов")
            
            return ProjectsData(
                categories=categories,
                projects=projects,
                last_updated=last_updated
            )
        except Exception as e:
            logger.error(f"Ошибка при загрузке кэша: {e}")
            return None


# Глобальный экземпляр парсера
parser = ProjectsParser()
