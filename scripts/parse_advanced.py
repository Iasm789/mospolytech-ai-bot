#!/usr/bin/env python3
"""
Расширенный парсер с обходом защиты от ботов
Использует несколько стратегий для получения достоверных данных
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
import re
import random
from urllib.parse import urljoin

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("❌ Playwright не установлен. Устанавливаю...")
    import subprocess
    subprocess.run(['pip', 'install', 'playwright'], check=True)
    subprocess.run(['playwright', 'install'], check=True)
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedMosPolyParser:
    """Продвинутый парсер с множественными стратегиями"""
    
    def __init__(self):
        self.base_url = "https://mospolytech.ru/postupayushchim/programmy-obucheniya/bakalavriat/"
        self.programs: Set[tuple] = set()  # Используем set для дедубликации
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
    
    async def parse_all_strategies(self) -> bool:
        """Попробовать все доступные стратегии парсинга"""
        strategies = [
            ("Основная страница с Playwright", self._strategy_main_page),
            ("Страницы факультетов", self._strategy_faculty_pages),
            ("API запросы (если доступны)", self._strategy_api_requests),
            ("Кэшированные данные", self._strategy_use_cached),
        ]
        
        for name, strategy in strategies:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Стратегия: {name}")
            logger.info(f"{'='*60}")
            try:
                if await strategy():
                    logger.info(f"✅ Стратегия '{name}' успешна!")
                    return True
            except Exception as e:
                logger.warning(f"⚠️  Ошибка в стратегии: {e}")
                continue
        
        return len(self.programs) > 0
    
    async def _strategy_main_page(self) -> bool:
        """Стратегия 1: Загрузка основной страницы"""
        logger.info("Попытка загрузки основной страницы со всеми программами...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                locale='ru-RU',
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True,
            )
            
            page = await context.new_page()
            
            try:
                # Добавляем человеческие параметры
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                """)
                
                logger.info(f"⏳ Загружаю {self.base_url}...")
                await page.goto(self.base_url, wait_until='networkidle', timeout=60000)
                
                # Проверяем капчу
                if await self._handle_captcha(page):
                    logger.warning("⚠️  Капча требует взаимодействия. Ждем...")
                    await asyncio.sleep(5)
                
                # Ждем загрузки контента
                await self._wait_for_programs(page)
                
                # Скролим для ленивой загрузки
                await self._scroll_page(page)
                
                # Парсим вкусные программы
                programs = await self._extract_programs(page)
                
                for prog in programs:
                    self.programs.add(tuple(sorted(prog.items())))
                
                logger.info(f"✅ Найдено {len(programs)} программ")
                return len(programs) > 5
                
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def _strategy_faculty_pages(self) -> bool:
        """Стратегия 2: Загрузка со страниц факультетов"""
        logger.info("Загружаю программы со страниц факультетов...")
        
        faculty_pages = [
            "https://mospolytech.ru/postupayushchim/programmy-obucheniya/",
            "https://mospolytech.ru/postupayushchim/nachalnym-bakalavratom/",
            "https://mospolytech.ru/estructure/faculties/",
        ]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            for faculty_url in faculty_pages:
                logger.info(f"📖 Загружаю {faculty_url}...")
                context = await browser.new_context(user_agent=random.choice(self.user_agents))
                page = await context.new_page()
                
                try:
                    await page.goto(faculty_url, wait_until='load', timeout=40000)
                    await self._scroll_page(page)
                    
                    programs = await self._extract_programs(page)
                    for prog in programs:
                        self.programs.add(tuple(sorted(prog.items())))
                    
                    logger.info(f"✅ Загружено {len(programs)} программ со страницы")
                except Exception as e:
                    logger.debug(f"Ошибка с этой страницей: {e}")
                finally:
                    await context.close()
            
            await browser.close()
        
        return len(self.programs) > 5
    
    async def _strategy_api_requests(self) -> bool:
        """Стратегия 3: API запросы (если сайт использует API)"""
        logger.info("Попытка загрузки через API...")
        
        api_endpoints = [
            "https://api.mospolytech.ru/programs",
            "https://mospolytech.ru/api/programs",
            "https://mospolytech.ru/wp-json/wp/v2/programs",
        ]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Пытаемся поймать сетевые запросы
                responses = []
                
                def handle_response(response):
                    if 'program' in response.url.lower() or response.status == 200:
                        responses.append(response)
                
                page.on('response', handle_response)
                
                await page.goto(self.base_url, wait_until='networkidle')
                
                # Проверяем поднятые запросы
                for response in responses:
                    try:
                        data = await response.json()
                        programs = self._extract_from_json(data)
                        for prog in programs:
                            self.programs.add(tuple(sorted(prog.items())))
                    except:
                        pass
                
                logger.info(f"✅ Найдено {len(self.programs)} программ через API")
                return len(self.programs) > 5
                
            except Exception as e:
                logger.debug(f"API стратегия не сработала: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def _strategy_use_cached(self) -> bool:
        """Стратегия 4: Использование кэшированных данных, если есть"""
        logger.info("Проверка кэшированных данных...")
        
        cache_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    programs = data.get('programs', [])
                    for prog in programs:
                        if isinstance(prog, dict):
                            self.programs.add(tuple(sorted(prog.items())))
                    
                    logger.info(f"✅ Загружено {len(programs)} программ из кэша")
                    return len(programs) > 5
            except Exception as e:
                logger.debug(f"Ошибка при чтении кэша: {e}")
        
        return False
    
    async def _handle_captcha(self, page: Page) -> bool:
        """Обработка капчи"""
        try:
            captcha_elements = await page.query_selector_all(
                'iframe[src*="captcha"], [class*="captcha"], .g-recaptcha'
            )
            
            if captcha_elements:
                logger.warning("🚫 Обнаружена капча. Попытка обхода...")
                
                # Пытаемся найти и кликнуть на чекбокс капчи
                try:
                    await page.wait_for_selector('label', timeout=3000)
                    elements = await page.query_selector_all('label')
                    if elements:
                        await elements[0].click()
                        logger.info("✅ Попытка клика на капчу")
                        await asyncio.sleep(3)
                except:
                    pass
                
                return True
            
            return False
        except:
            return False
    
    async def _wait_for_programs(self, page: Page):
        """Ждем загрузки элементов программ"""
        selectors = [
            '[class*="program"]',
            '[class*="card"]',
            '.program-item',
            'article',
            '.post',
            '[data-program]',
        ]
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                logger.info(f"✅ Найдены элементы по селектору: {selector}")
                return
            except:
                continue
    
    async def _scroll_page(self, page: Page):
        """Скролл страницы для загрузки ленивых элементов"""
        logger.info("📜 Скролю страницу для загрузки всех элементов...")
        try:
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = window.innerHeight;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 1000);
                    });
                }
            """)
        except:
            # Fallback для простого скролла
            for _ in range(10):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(0.5)
    
    async def _extract_programs(self, page: Page) -> List[Dict]:
        """Извлечь программы со страницы"""
        programs = []
        
        try:
            # Получаем все текстовые элементы
            content = await page.content()
            
            # Ищем JSON в скриптах
            json_match = re.search(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', 
                                  content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    programs.extend(self._extract_from_json(data))
                except:
                    pass
            
            # Парсим HTML элементы
            text_content = await page.evaluate('document.body.innerText')
            
            # Ищем названия программ с кодами специальностей
            pattern = r'([А-Яа-я\s\-\.]+?)\s+(\d{2}\.\d{2}\.\d{2})'
            matches = re.findall(pattern, text_content)
            
            for title, code in matches:
                title = title.strip()
                if len(title) > 3 and len(title) < 150:
                    program = {
                        'title': title,
                        'code': code,
                        'source': 'web_parsed',
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    # Дедубликируем по названию и коду
                    if not any(p['title'] == title and p.get('code') == code for p in programs):
                        programs.append(program)
            
            logger.info(f"📊 Извлечено {len(programs)} уникальных программ")
            return programs
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении: {e}")
            return programs
    
    def _extract_from_json(self, obj: any, path: str = "") -> List[Dict]:
        """Рекурсивно ищет программы в JSON"""
        programs = []
        
        if isinstance(obj, dict):
            # Проверяем, это ли программа
            if self._is_program_dict(obj):
                programs.append(obj)
            
            # Ищем в значениях
            for key, value in obj.items():
                programs.extend(self._extract_from_json(value, f"{path}.{key}"))
        
        elif isinstance(obj, list):
            for item in obj:
                programs.extend(self._extract_from_json(item, f"{path}[]"))
        
        return programs
    
    def _is_program_dict(self, obj: dict) -> bool:
        """Проверить, является ли словарь программой обучения"""
        program_keys = ['title', 'name', 'program', 'direction', 'specialization', 'code', 'specialty']
        has_name = any(key in obj for key in ['title', 'name'])
        
        if has_name and len(obj) > 0:
            return True
        
        return False
    
    def get_programs_as_list(self) -> List[Dict]:
        """Получить программы как список словарей"""
        result = []
        for prog_tuple in self.programs:
            prog_dict = dict(prog_tuple)
            result.append(prog_dict)
        return result
    
    def save_to_json(self, output_file: Optional[Path] = None) -> bool:
        """Сохранить результаты"""
        if not output_file:
            output_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            programs = self.get_programs_as_list()
            
            # Группируем по факультетам
            faculties_dict = {}
            for prog in programs:
                faculty = prog.get('faculty_name', 'Неизвестный факультет')
                if faculty not in faculties_dict:
                    faculties_dict[faculty] = []
                faculties_dict[faculty].append(prog)
            
            result = {
                'source': self.base_url,
                'programs': programs,
                'count': len(programs),
                'by_faculty': {name: len(progs) for name, progs in faculties_dict.items()},
                'last_updated': datetime.now().isoformat(),
                'note': 'Данные получены путем парсинга официального сайта МосПолитеха',
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Сохранено {len(programs)} программ в {output_file}")
            logger.info(f"   По факультетам: {result['by_faculty']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении: {e}")
            return False


async def main():
    """Главная функция"""
    parser = AdvancedMosPolyParser()
    
    logger.info("🚀 Запускаю продвинутый парсер МосПолитеха")
    logger.info(f"📌 Целевой URL: {parser.base_url}")
    
    success = await parser.parse_all_strategies()
    
    if success:
        logger.info(f"\n✅ УСПЕХ! Найдено {len(parser.programs)} программ")
        parser.save_to_json()
        return True
    else:
        logger.error(f"\n❌ ОШИБКА: Не удалось загрузить программы")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
