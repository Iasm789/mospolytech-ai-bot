import json
from pathlib import Path
from collections import defaultdict

cache_file = Path('data/cache/programs_cache.json')
with open(cache_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

faculties = data['faculties']
programs = data['programs']

print('='*70)
print('✅ ИТОГОВАЯ СТАТИСТИКА КЭША ПРОГРАММ')
print('='*70)
print(f'\n📁 Файл кэша: {cache_file}')
print(f'💾 Размер: {cache_file.stat().st_size / 1024:.1f} KB')

print(f'\n📦 Всего элементов:')
print(f'   • Факультеты: {len(faculties)}')
print(f'   • Программы: {len(programs)}')

print(f'\n🏛️ Список факультетов с исправленными названиями:')
for fac in faculties:
    fac_name = fac['name']
    print(f'   • {fac_name:<55} (id: {fac["id"]})')

print(f'\n📊 Распределение программ:')
stats = defaultdict(int)
for prog in programs:
    stats[prog['faculty_name']] += 1

for faculty, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f'   • {faculty:<50}: {count:2d} программ')

print(f'\n✨ Примеры новых программ:')
new_progs = ['Кибербезопасность и защита данных', 'Возобновляемые источники энергии', 
             'Автономные и беспилотные системы', 'Цифровая экономика', 'Анимация и мультимедия']
for prog_title in new_progs:
    found = next((p for p in programs if p['title'] == prog_title), None)
    if found:
        print(f'   • {found["title"]:<40} ({found["faculty_name"]})')

print('='*70)
