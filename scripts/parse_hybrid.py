#!/usr/bin/env python3
"""
Гибридный парсер МосПолитеха - фактический сбор достоверных данных
Комбинирует множественные методы с обходом защиты от ботов
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple
import re
import random
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ Playwright не установлен. Установите: pip install playwright")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridMosPolyParser:
    """Гибридный парсер для получения программ МосПолитеха"""
    
    def __init__(self):
        self.base_url = "https://mospolytech.ru/postupayushchim/programmy-obucheniya/bakalavriat/"
        self.programs: Dict[str, Dict] = {}  # Код -> программа
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
    
    async def parse_complete(self) -> bool:
        """Полный парсинг всеми методами"""
        logger.info("=" * 80)
        logger.info("🚀 СТАРТ ГИБРИДНОГО ПАРСЕРА МОСПОЛИТЕХА")
        logger.info("=" * 80)
        
        # Метод 1: Прямая загрузка со страницы
        logger.info("\n[1/3] Метод: Загрузка основной страницы")
        await self._method_main_page()
        
        if len(self.programs) > 40:
            logger.info(f"✅ Достаточно программ найдено: {len(self.programs)}")
            return True
        
        # Метод 2: Загрузка с поиска по факультетам
        logger.info("\n[2/3] Метод: Загрузка с фильтрацией по факультетам")
        await self._method_faculty_filter()
        
        if len(self.programs) > 40:
            logger.info(f"✅ Достаточно программ найдено: {len(self.programs)}")
            return True
        
        # Метод 3: Загрузка со страниц справочника
        logger.info("\n[3/3] Метод: Загрузка из справочника (каталог программ)")
        await self._method_catalog()
        
        logger.info("\n" + "=" * 80)
        logger.info(f"📊 ИТОГО: {len(self.programs)} программ загружено")
        logger.info("=" * 80)
        
        return len(self.programs) > 20
    
    async def _method_main_page(self):
        """Метод 1: Загрузка со страницы бакалавриата"""
        logger.info("⏳ Загружаю основную страницу со всеми программами...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=self._get_browser_args()
            )
            
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080},
                locale='ru-RU',
            )
            
            page = await context.new_page()
            
            try:
                # Добавляем скрипт для маскировки бота
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => false});
                    window.chrome = {runtime: {}};
                """)
                
                await page.goto(self.base_url, wait_until='networkidle', timeout=60000)
                
                # Специальная обработка для капчи
                await self._handle_page_captcha(page)
                
                # Скролим для загрузки ленивых элементов
                await self._smart_scroll(page)
                
                # Парсим программы
                programs = await self._extract_all_programs(page)
                self._add_programs(programs)
                
                logger.info(f"✅ Найдено {len(programs)} программ с основной страницы")
                
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
            finally:
                await context.close()
                await browser.close()
    
    async def _method_faculty_filter(self):
        """Метод 2: Загрузка с фильтрацией по факультетам"""
        logger.info("⏳ Загружаю программы с фильтрацией по факультетам...")
        
        faculty_codes = [
            'fit', 'fm', 'fche', 'ft', 'f_ekonomiki', 
            'f_iskusstva', 'f_izdatelskogo', 'f_poligraficheskogo', 
            'f_urbanistiki'
        ]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            for faculty_id in faculty_codes:
                url = f"{self.base_url}?faculty={faculty_id}"
                logger.info(f"  📖 Загружаю факультет: {faculty_id}")
                
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents)
                )
                page = await context.new_page()
                
                try:
                    await page.goto(url, wait_until='load', timeout=40000)
                    await asyncio.sleep(2)
                    
                    programs = await self._extract_all_programs(page)
                    for prog in programs:
                        prog['faculty_id'] = faculty_id
                    
                    self._add_programs(programs)
                    logger.info(f"     ✅ Получено {len(programs)} программ")
                    
                except Exception as e:
                    logger.debug(f"     Ошибка: {e}")
                finally:
                    await context.close()
            
            await browser.close()
    
    async def _method_catalog(self):
        """Метод 3: Загрузка из каталога программ"""
        logger.info("⏳ Загружаю программы из справочника...")
        
        catalog_urls = [
            "https://mospolytech.ru/postupayushchim/programmy-obucheniya/",
            "https://mospolytech.ru/estruture/faculties/",
        ]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            for url in catalog_urls:
                logger.info(f"  📚 Загружаю {url}")
                
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents)
                )
                page = await context.new_page()
                
                try:
                    await page.goto(url, wait_until='load', timeout=40000)
                    await self._smart_scroll(page)
                    
                    programs = await self._extract_all_programs(page)
                    self._add_programs(programs)
                    logger.info(f"    ✅ Получено {len(programs)} программ")
                    
                except Exception as e:
                    logger.debug(f"    Ошибка: {e}")
                finally:
                    await context.close()
            
            await browser.close()
    
    def _get_browser_args(self) -> List[str]:
        """Аргументы браузера для обхода защиты"""
        return [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-setuid-sandbox',
        ]
    
    async def _handle_page_captcha(self, page: Page):
        """Обработка капчи на странице"""
        try:
            # Проверяем наличие капчи
            iframes = await page.query_selector_all('iframe')
            for iframe in iframes:
                src = await iframe.get_attribute('src')
                if src and ('captcha' in src.lower() or 'yandex' in src.lower()):
                    logger.warning("⚠️  Обнаружена капча. Попытка обхода...")
                    
                    # Ждем и пытаемся взаимодействовать
                    await asyncio.sleep(2)
                    
                    # Пытаемся найти чекбокс
                    try:
                        checkboxes = await page.query_selector_all('input[type="checkbox"]')
                        if checkboxes:
                            await checkboxes[0].click()
                            logger.info("✅ Попытка клика на чекбокс капчи")
                            await asyncio.sleep(3)
                    except:
                        pass
            
            return True
        except:
            return False
    
    async def _smart_scroll(self, page: Page):
        """Умный скролл для загрузки ленивых элементов"""
        logger.info("📜 Скролю для загрузки всех элементов...")
        
        try:
            await page.evaluate("""
                async () => {
                    let lastScrollTop = 0;
                    while(true) {
                        const scrollHeight = document.documentElement.scrollHeight;
                        window.scrollBy(0, window.innerHeight);
                        
                        await new Promise(r => setTimeout(r, 500));
                        
                        const newScrollTop = window.scrollY;
                        if(newScrollTop === lastScrollTop) break;
                        
                        lastScrollTop = newScrollTop;
                    }
                    window.scrollTo(0, 0);
                }
            """)
        except:
            # Fallback
            for _ in range(10):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(0.3)
    
    async def _extract_all_programs(self, page: Page) -> List[Dict]:
        """Извлечь все программы со страницы"""
        programs = []
        
        try:
            content = await page.content()
            text_content = await page.evaluate('document.body.innerText')
            
            # Парсим из HTML контента
            html_programs = self._parse_html_text(text_content, content)
            programs.extend(html_programs)
            
            logger.info(f"📊 Извлечено {len(programs)} программ")
            return programs
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении: {e}")
            return []
    
    def _parse_html_text(self, text: str, html: str) -> List[Dict]:
        """Парсить программы из текста HTML"""
        programs = []
        
        # Ищем коды специальностей и названия
        # Формат: Название программы (код)
        # Есть возможность, что код идет после названия
        
        # Паттерн 1: "Название" \d\d.\d\d.\d\d
        pattern1 = r'([А-Яа-я\s\-\.,\(\)]{5,120}?)\s*(\d{2}\.\d{2}\.\d{2})'
        
        matches = set()
        for match in re.finditer(pattern1, text):
            title = match.group(1).strip()
            code = match.group(2)
            
            # Фильтруем шум
            if len(title) > 5 and len(title) < 150:
                # Убираем лишние символы
                title = re.sub(r'\s+', ' ', title).strip()
                title = re.sub(r'[^\w\s\-\.]', '', title, flags=re.UNICODE)
                
                key = (code, title)
                if key not in matches and code and title:
                    matches.add(key)
        
        # Преобразуем в программы
        for code, title in matches:
            program = {
                'code': code,
                'title': title,
                'url': self.base_url,
                'source': 'parsed',
                'parsed_at': datetime.now().isoformat(),
            }
            
            # Определяем направленность
            if 'информационн' in title.lower():
                program['faculty_name'] = 'Факультет информационных технологий'
                program['faculty_id'] = 'fit'
            elif 'машиностроени' in title.lower():
                program['faculty_name'] = 'Факультет машиностроения'
                program['faculty_id'] = 'fm'
            elif 'химическ' in title.lower() or 'биотехнолог' in title.lower():
                program['faculty_name'] = 'Факультет химической технологии'
                program['faculty_id'] = 'fche'
            elif 'транспорт' in title.lower():
                program['faculty_name'] = 'Факультет транспорта'
                program['faculty_id'] = 'ft'
            elif 'экономик' in title.lower() or 'менеджмент' in title.lower():
                program['faculty_name'] = 'Факультет экономики и управления'
                program['faculty_id'] = 'f_ekonomiki'
            elif 'дизайн' in title.lower() or 'искусств' in title.lower():
                program['faculty_name'] = 'Факультет графики и искусства'
                program['faculty_id'] = 'f_iskusstva'
            elif 'издательск' in title.lower() or 'журналист' in title.lower():
                program['faculty_name'] = 'Факультет издательского дела'
                program['faculty_id'] = 'f_izdatelskogo'
            elif 'полиграф' in title.lower():
                program['faculty_name'] = 'Факультет полиграфический'
                program['faculty_id'] = 'f_poligraficheskogo'
            elif 'архитектур' in title.lower() or 'городск' in title.lower() or 'строител' in title.lower():
                program['faculty_name'] = 'Факультет урбанистики'
                program['faculty_id'] = 'f_urbanistiki'
            
            programs.append(program)
        
        return programs
    
    def _add_programs(self, programs: List[Dict]):
        """Добавить программы, избегая дубликатов"""
        for prog in programs:
            code = prog.get('code')
            if code:
                if code not in self.programs:
                    self.programs[code] = prog
                else:
                    # Обновляем информацию если есть дополнительные данные
                    self.programs[code].update({k: v for k, v in prog.items() 
                                               if v and k != 'code'})
    
    def get_programs_list(self) -> List[Dict]:
        """Получить список программ"""
        return list(self.programs.values())
    
    def save_cache(self, output_file: Path = None) -> bool:
        """Сохранить результаты"""
        if not output_file:
            output_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            programs = self.get_programs_list()
            
            # Группируем по факультетам
            faculties_summary = {}
            for prog in programs:
                fac = prog.get('faculty_name', 'Неизвестный')
                if fac not in faculties_summary:
                    faculties_summary[fac] = 0
                faculties_summary[fac] += 1
            
            result = {
                'source': self.base_url,
                'programs': programs,
                'statistics': {
                    'total_programs': len(programs),
                    'by_faculty': faculties_summary,
                },
                'last_updated': datetime.now().isoformat(),
                'note': 'Достоверные данные получены путем парсинга официального сайта МосПолитеха',
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"\n✅ СОХРАНЕНО:")
            logger.info(f"   Файл: {output_file}")
            logger.info(f"   Программ: {len(programs)}")
            for fac, count in sorted(faculties_summary.items()):
                logger.info(f"   - {fac}: {count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении: {e}")
            return False


async def main():
    """Главная функция"""
    parser = HybridMosPolyParser()
    
    try:
        success = await parser.parse_complete()
        
        if success:
            parser.save_cache()
            return True
        else:
            logger.error("❌ Не удалось загрузить достаточное количество программ")
            return False
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Прервано пользователем")
        return False
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
