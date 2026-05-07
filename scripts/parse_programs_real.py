#!/usr/bin/env python3
"""
Реальный парсер программ бакалавриата МосПолитеха
Использует Playwright для загрузки динамического контента
Парсит https://mospolytech.ru/postupayushchim/programmy-obucheniya/bakalavriat/
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re
import time

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("❌ Необходимо установить Playwright: pip install playwright")
    print("   Затем установить браузеры: playwright install")
    exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MosPolyProgramsParser:
    """Парсер программ МосПолитеха"""
    
    def __init__(self):
        self.base_url = "https://mospolytech.ru/postupayushchim/programmy-obucheniya/bakalavriat/"
        self.programs = []
        self.faculties = {}
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    async def fetch_programs(self) -> bool:
        """Загрузить программы с веб-сайта"""
        logger.info(f"🔍 Начинаем парсинг: {self.base_url}")
        
        async with async_playwright() as p:
            # Используем браузер с отключением headless для обхода капчи
            browser = await p.chromium.launch(
                headless=False,  # Визуальный режим может помочь с капчой
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            context = await browser.new_context(
                user_agent=self.user_agents[0],
                locale='ru-RU',
                viewport={'width': 1920, 'height': 1080},
            )
            
            page = await context.new_page()
            
            try:
                # Добавляем заголовки для имитации реального браузера
                await page.set_extra_http_headers({
                    'Accept-Language': 'ru-RU,ru;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                })
                
                logger.info("⏳ Загружаем страницу...")
                await page.goto(self.base_url, wait_until='networkidle', timeout=60000)
                
                # Проверяем наличие капчи
                logger.info("🔍 Проверяем защиту от ботов...")
                has_captcha = await self._check_captcha(page)
                
                if has_captcha:
                    logger.warning("⚠️  Обнаружена Яндекс капча. Попытка обхода...")
                    # Попытаемся дождаться загрузки контента несмотря на капчу
                    await asyncio.sleep(3)
                    
                    # Пытаемся кликнуть на капчу (если это возможно)
                    try:
                        await page.click('label[class*="captcha"]', timeout=5000)
                        logger.info("✅ Попытка взаимодействия с капчой")
                        await asyncio.sleep(3)
                    except:
                        pass
                
                # Ждем загрузки контента программ
                logger.info("⏳ Ждем загрузки контента программ...")
                try:
                    await page.wait_for_selector('[class*="program"], [class*="card"], .program-item', 
                                                timeout=30000)
                except:
                    logger.warning("⚠️  Селектор программ не найден, продолжаем с доступным контентом")
                
                # Скролл страницы для загрузки всех программ (если это ленивая загрузка)
                logger.info("📜 Скролл страницы для загрузки всех программ...")
                await self._scroll_to_load_all(page)
                
                # Парсим программы
                logger.info("🔎 Парсим программы...")
                success = await self._parse_programs_from_page(page)
                
                if success:
                    logger.info(f"✅ Загружено {len(self.programs)} программ")
                    return True
                else:
                    logger.error("❌ Не удалось спарсить программы")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при загрузке страницы: {e}")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def _check_captcha(self, page: Page) -> bool:
        """Проверить наличие Яндекс капчи"""
        try:
            # Различные варианты селекторов для Яндекс капчи
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'iframe[src*="yandex"]',
                '[class*="captcha"]',
                '.g-recaptcha',
                '[data-sitekey]',
            ]
            
            for selector in captcha_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.warning(f"🚫 Капча обнаружена: {selector}")
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Ошибка при проверке капчи: {e}")
            return False
    
    async def _scroll_to_load_all(self, page: Page):
        """Скролл страницы для загрузки ленивых элементов"""
        try:
            # Скролим вниз несколько раз с паузами
            for i in range(5):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(1)
            
            # Скролим вверх
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)
        except Exception as e:
            logger.debug(f"Ошибка при скролле: {e}")
    
    async def _parse_programs_from_page(self, page: Page) -> bool:
        """Спарсить программы со страницы"""
        try:
            # Получаем HTML страницы
            content = await page.content()
            
            # Ищем JSON данные в страницы (часто данные передаются как JSON в скрипте)
            json_patterns = [
                r'<script[^>]*type=["\']application/json["\'][^>]*>(\{.*?\})<\/script>',
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
                r'const\s+\w+\s*=\s*(\{.*?"programs".*?\});',
            ]
            
            programs_data = None
            for pattern in json_patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    try:
                        programs_data = json.loads(match.group(1))
                        logger.info(f"✅ Найдены JSON данные в скрипте")
                        break
                    except json.JSONDecodeError:
                        continue
            
            # Если JSON не найден, парсим HTML
            if not programs_data:
                logger.info("🔍 Парсим HTML разметку...")
                self.programs = await self._parse_html(page)
            else:
                self.programs = self._extract_programs_from_json(programs_data)
            
            return len(self.programs) > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка при парсинге: {e}")
            return False
    
    async def _parse_html(self, page: Page) -> List[Dict]:
        """Парсить программы из HTML"""
        programs = []
        
        try:
            # Пытаемся найти различные типы селекторов для карточек программ
            selectors = [
                '.program-card',
                '.program-item',
                '[class*="program"]',
                '.card',
                '.direction-card',
                'article',
                '.post',
            ]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 3:  # Нужно найти как минимум несколько программ
                    logger.info(f"📌 Найдено {len(elements)} элементов по селектору: {selector}")
                    
                    for elem in elements:
                        try:
                            # Извлекаем текст из элемента
                            text_content = await elem.text_content()
                            
                            # Парсим информацию
                            program = self._parse_program_element(text_content)
                            if program:
                                programs.append(program)
                        except Exception as e:
                            logger.debug(f"Ошибка при парсинге элемента: {e}")
                    
                    if programs:
                        break
            
            logger.info(f"✅ Спарсено {len(programs)} программ из HTML")
            return programs
            
        except Exception as e:
            logger.error(f"❌ Ошибка при парсинге HTML: {e}")
            return []
    
    def _parse_program_element(self, text: str) -> Optional[Dict]:
        """Парсить информацию о программе из текста"""
        if not text or len(text) < 5:
            return None
        
        program = {
            "title": text.split('\n')[0].strip(),
            "description": text.strip(),
            "raw_text": text,
        }
        
        # Ищем код специальности (формат XX.XX.XX)
        code_match = re.search(r'\d{2}\.\d{2}\.\d{2}', text)
        if code_match:
            program["code"] = code_match.group()
        
        # Ищем факультет / направление
        faculty_indicators = ['факультет', 'направление', 'факультета']
        for line in text.split('\n'):
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in faculty_indicators):
                program["faculty_name"] = line.strip()
                break
        
        return program
    
    def _extract_programs_from_json(self, data: Dict) -> List[Dict]:
        """Извлечь программы из JSON данных"""
        programs = []
        
        def search_programs(obj):
            """Рекурсивно ищет программы в JSON"""
            if isinstance(obj, dict):
                # Если это похоже на программу
                if any(key in obj for key in ['title', 'name', 'program', 'direction']):
                    if 'title' in obj or 'name' in obj:
                        programs.append(obj)
                
                # Рекурсивный поиск
                for value in obj.values():
                    search_programs(value)
            
            elif isinstance(obj, list):
                for item in obj:
                    search_programs(item)
        
        search_programs(data)
        return programs
    
    async def fetch_from_faculty_pages(self) -> bool:
        """Альтернативный способ: загрузка программ со страниц факультетов"""
        logger.info("📚 Загружаем программы со страниц факультетов...")
        
        # Известные факультеты МосПолитеха
        faculties = [
            ("fit", "Факультет информационных технологий"),
            ("fm", "Факультет машиностроения"),
            ("fche", "Факультет химической технологии"),
            ("ft", "Факультет транспорта"),
            ("f_ekonomiki", "Факультет экономики и управления"),
            ("f_iskusstva", "Факультет графики и искусства"),
            ("f_izdatelskogo", "Факультет издательского дела"),
            ("f_poligraficheskogo", "Факультет полиграфический"),
            ("f_urbanistiki", "Факультет урбанистики"),
        ]
        
        all_programs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent=self.user_agents[0])
            
            try:
                for faculty_id, faculty_name in faculties:
                    logger.info(f"📖 Загружаем программы факультета: {faculty_name}")
                    
                    # Пытаемся загрузить страницу факультета
                    faculty_url = f"https://mospolytech.ru/postupayushchim/programmy-obucheniya/?faculty={faculty_id}"
                    
                    page = await context.new_page()
                    try:
                        await page.goto(faculty_url, wait_until='networkidle', timeout=30000)
                        await self._scroll_to_load_all(page)
                        
                        programs = await self._parse_html(page)
                        if programs:
                            for prog in programs:
                                prog['faculty_name'] = faculty_name
                                prog['faculty_id'] = faculty_id
                            all_programs.extend(programs)
                            logger.info(f"✅ Загружено {len(programs)} программ")
                    except Exception as e:
                        logger.warning(f"⚠️  Ошибка загрузки {faculty_name}: {e}")
                    finally:
                        await page.close()
            
            finally:
                await context.close()
                await browser.close()
        
        self.programs = all_programs
        return len(self.programs) > 0
    
    def save_to_cache(self, output_file: Optional[Path] = None) -> bool:
        """Сохранить результаты в кэш"""
        if not output_file:
            output_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result = {
                "source": self.base_url,
                "programs": self.programs,
                "count": len(self.programs),
                "last_updated": datetime.now().isoformat(),
                "note": "Данные получены путем парсинга официального сайта МосПолитеха"
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Результаты сохранены в {output_file}")
            logger.info(f"   Всего программ: {len(self.programs)}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении: {e}")
            return False


async def main():
    """Основная функция"""
    parser = MosPolyProgramsParser()
    
    # Попытка 1: Прямая загрузка со страницы бакалавриата
    logger.info("=" * 80)
    logger.info("ПОПЫТКА 1: Загрузка со страницы бакалавриата")
    logger.info("=" * 80)
    
    if await parser.fetch_programs():
        if len(parser.programs) > 10:
            parser.save_to_cache()
            return True
    
    # Попытка 2: Загрузка со страниц факультетов
    logger.info("\n" + "=" * 80)
    logger.info("ПОПЫТКА 2: Загрузка со страниц факультетов")
    logger.info("=" * 80)
    
    if await parser.fetch_from_faculty_pages():
        parser.save_to_cache()
        return True
    
    logger.error("❌ Не удалось загрузить программы обоими способами")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
