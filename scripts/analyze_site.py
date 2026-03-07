#!/usr/bin/env python3
"""
Утилита для тестирования и анализа структуры сайта МосПолитеха
Помогает выявить источник данных для парсинга
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import re

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright не установлен")
    exit(1)

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def analyze_site_structure():
    """Анализировать структуру и источники данных на сайте"""
    
    url = "https://mospolytech.ru/postupayushchim/programmy-obucheniya/bakalavriat/"
    
    logger.info(f"🔍 Анализирую структуру сайта: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Собираем сетевые запросы
        network_log = []
        
        def log_request(request):
            network_log.append({
                'method': request.method,
                'url': request.url,
                'resource_type': request.resource_type,
            })
        
        page.on('request', log_request)
        
        try:
            logger.info("⏳ Загружаю страницу...")
            await page.goto(url, wait_until='networkidle')
            
            # Даем время на загрузку JS
            await asyncio.sleep(3)
            
            # Анализируем содержимое
            content = await page.content()
            
            # 1. Ищем JSON данные
            logger.info("\n📊 АНАЛИЗ JSON ДАННЫХ:")
            json_patterns = re.findall(r'<script[^>]*>(\{.*?\})<\/script>', content, re.DOTALL)
            logger.info(f"   Найдено скриптов с JSON: {len(json_patterns)}")
            
            for i, json_str in enumerate(json_patterns[:3]):  # Первые 3
                try:
                    data = json.loads(json_str[:200])  # Первые 200 символов
                    logger.info(f"   JSON #{i+1} ключи: {list(data.keys())[:5]}")
                except:
                    pass
            
            # 2. Ищем API вызовы
            logger.info("\n🌐 АНАЛИЗ СЕТЕВЫХ ЗАПРОСОВ:")
            api_requests = [r for r in network_log if 'api' in r['url'].lower() or 'ajax' in r['url'].lower()]
            logger.info(f"   Всего запросов: {len(network_log)}")
            logger.info(f"   API запросов: {len(api_requests)}")
            
            for req in api_requests[:5]:
                logger.info(f"   - {req['method']} {req['url'][:80]}")
            
            # 3. Ищем данные о программах
            logger.info("\n📚 АНАЛИЗ КОНТЕНТА ПРОГРАММ:")
            
            # Ищем коды специальностей
            program_codes = set(re.findall(r'\d{2}\.\d{2}\.\d{2}', content))
            logger.info(f"   Найдено уникальных кодов специальностей: {len(program_codes)}")
            if program_codes:
                logger.info(f"   Примеры: {list(program_codes)[:5]}")
            
            # Ищем названия программ
            program_names = set(re.findall(r'([А-Яа-я\s\-]{10,100})(?:\s+\d{2}\.\d{2}\.\d{2}|факультет)', content))
            logger.info(f"   Найдено потенциальных названий программ: {len(program_names)}")
            
            # 4. Анализируем элементы DOM
            logger.info("\n🏗️  АНАЛИЗ СТРУКТУРЫ DOM:")
            
            selectors_to_check = [
                '[class*="program"]',
                '[class*="card"]',
                '.program-item',
                'article',
                '[data-program]',
                '.direction',
                '.specialty',
            ]
            
            for selector in selectors_to_check:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"   ✅ '{selector}' -> {len(elements)} элементов")
                except:
                    pass
            
            # 5. Проверяем наличие капчи
            logger.info("\n🔐 АНАЛИЗ ЗАЩИТЫ:")
            captcha_indicators = [
                'captcha',
                'yandex',
                'recaptcha',
                'hcaptcha',
            ]
            
            for indicator in captcha_indicators:
                if indicator.lower() in content.lower():
                    logger.warning(f"   🚫 Обнаружена защита: {indicator}")
            
            # 6. Ищем скрытые JSON в атрибутах
            logger.info("\n💾 АНАЛИЗ СКРЫТЫХ ДАННЫХ:")
            json_attrs = re.findall(r'data-[a-z-]*="(\{.*?\})"', content)
            logger.info(f"   JSON в data-атрибутах: {len(json_attrs)}")
            
            # 7. Получаем текстовый контент
            logger.info("\n📄 ТЕКСТОВЫЙ КОНТЕНТ:")
            text = await page.evaluate('document.body.innerText')
            
            # Ищем программы в тексте
            lines = text.split('\n')
            program_lines = [l for l in lines if any(code in l for code in program_codes)]
            logger.info(f"   Строк с кодами программ: {len(program_lines)}")
            if program_lines:
                logger.info("   Примеры:")
                for line in program_lines[:5]:
                    logger.info(f"     - {line.strip()[:100]}")
            
            # 8. Сохраняем результаты анализа
            logger.info("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ:")
            
            analysis_result = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'findings': {
                    'total_network_requests': len(network_log),
                    'api_requests': len(api_requests),
                    'unique_program_codes': len(program_codes),
                    'found_program_codes': list(program_codes)[:20],
                    'program_codes_count': len(program_codes),
                    'captcha_detected': any(c.lower() in content.lower() 
                                           for c in ['captcha', 'yandex', 'recaptcha']),
                    'api_requests_list': [
                        {'method': r['method'], 'url': r['url']} 
                        for r in api_requests[:10]
                    ],
                },
            }
            
            output_file = Path(__file__).parent.parent / "data" / "site_analysis.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Результаты анализа сохранены в {output_file}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе: {e}")
            return None
        finally:
            await context.close()
            await browser.close()


async def test_direct_api_access():
    """Тестировние прямого доступа к API"""
    logger.info("\n🧪 ТЕСТИРОВАНИЕ ПРЯМОГО API ДОСТУПА:")
    
    api_endpoints = [
        "https://mospolytech.ru/api/programs/",
        "https://mospolytech.ru/api/bakalavriat/",
        "https://api.mospolytech.ru/programs",
        "https://mospolytech.ru/wp-json/wp/v2/programs",
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        for endpoint in api_endpoints:
            logger.info(f"   Проверяю {endpoint}...")
            page = await context.new_page()
            try:
                response = await page.goto(endpoint, timeout=10000)
                if response and response.ok:
                    content_type = response.headers.get('content-type', '')
                    logger.info(f"      ✅ Доступен! Content-Type: {content_type}")
                    
                    if 'application/json' in content_type:
                        text = await response.text()
                        data = json.loads(text)
                        logger.info(f"      Структура JSON: {list(data.keys())[:5]}")
                else:
                    logger.info(f"      ❌ Не доступен (код {response.status if response else 'N/A'})")
            except Exception as e:
                logger.info(f"      ❌ Ошибка: {str(e)[:50]}")
            finally:
                await page.close()
        
        await context.close()
        await browser.close()


async def main():
    logger.info("=" * 80)
    logger.info("АНАЛИЗ САЙТА МОСПОЛИТЕХА")
    logger.info("=" * 80)
    
    analysis = await analyze_site_structure()
    await test_direct_api_access()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ АНАЛИЗ ЗАВЕРШЕН")
    logger.info("=" * 80)
    
    if analysis and analysis['findings']['unique_program_codes'] > 0:
        logger.info(f"\n📊 ИТОГИ:")
        logger.info(f"   Найденных программ (по кодам): {analysis['findings']['unique_program_codes']}")
        logger.info(f"   Капча обнаружена: {'да' if analysis['findings']['captcha_detected'] else 'нет'}")
        logger.info(f"   API запросов: {analysis['findings']['api_requests']}")


if __name__ == "__main__":
    asyncio.run(main())
