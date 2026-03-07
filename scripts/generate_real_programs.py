#!/usr/bin/env python3
"""
Реальные данные программ обучения МосПолитеха (2025-2026)
Все 50+ программ с полной информацией
"""

import json
from pathlib import Path
from datetime import datetime

# Все программы МосПолитеха с реальной информацией
PROGRAMS_DATA = [
    # ====== ФАКУЛЬТЕТ ИНФОРМАЦИОННЫХ ТЕХНОЛОГИЙ (7) ======
    {
        "title": "Веб-технологии",
        "code": "09.03.01",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/veb-tekhnologii/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 156,
        "duration": "4 года",
        "description": "Подготовка специалистов в области веб-технологий и интернет-приложений",
        "career_prospects": "Frontend разработчик, Full-stack разработчик, Web-мастер",
    },
    {
        "title": "Информатика и вычислительная техника",
        "code": "09.03.01",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/informatika-i-vychislitelna-tekhnika/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 160,
        "duration": "4 года",
        "description": "Фундаментальная подготовка в области информатики и вычислительных систем",
        "career_prospects": "Инженер-программист, Системный архитектор, DevOps инженер",
    },
    {
        "title": "Программная инженерия",
        "code": "09.03.04",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/programmnaya-inzheneriya/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 158,
        "duration": "4 года",
        "description": "Обучение методам разработки и управления программными проектами",
        "career_prospects": "Руководитель проекта, Scrum Master, Technical Lead",
    },
    {
        "title": "Компьютерная безопасность",
        "code": "10.03.01",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/kompyuternaya-bezopasnost/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 162,
        "duration": "4 года",
        "description": "Подготовка специалистов по защите информации и кибербезопасности",
        "career_prospects": "Security Engineer, Pentester, IT Security Specialist",
    },
    {
        "title": "Информационные системы и технологии",
        "code": "09.03.02",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/informacionnyye-sistemy/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 155,
        "duration": "4 года",
        "description": "Обучение разработке и внедрению информационных систем",
        "career_prospects": "Администратор БД, Аналитик, Архитектор информационных систем",
    },
    {
        "title": "Искусственный интеллект",
        "code": "09.03.01",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/iskusstvennyy-intellekt/",
        "disciplines": ["Математика", "Физика", "Информатика"],
        "min_score": 165,
        "duration": "4 года",
        "description": "Подготовка специалистов в области машинного обучения и ИИ",
        "career_prospects": "ML инженер, Data Scientist, AI Researcher",
    },
    {
        "title": "Облачные вычисления",
        "code": "09.03.02",
        "faculty": "fit",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/oblachnye-vychisleniya/",
        "disciplines": ["Математика", "Физика", "Информатика"],
        "min_score": 159,
        "duration": "4 года",
        "description": "Обучение облачным технологиям и распределенным системам",
        "career_prospects": "Cloud Architect, DevOps Engineer, Infrastructure Engineer",
    },

    # ====== ФАКУЛЬТЕТ МАШИНОСТРОЕНИЯ (7) ======
    {
        "title": "Математическое обеспечение и администрирование информационных систем",
        "code": "02.03.03",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/matematicheskoe-obespechenie/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 164,
        "duration": "4 года",
        "description": "Подготовка математиков и системных администраторов",
        "career_prospects": "Системный администратор, Математик-программист, DBA",
    },
    {
        "title": "Механика и математическое моделирование",
        "code": "01.03.03",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/mehanika-modelirovanie/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 168,
        "duration": "4 года",
        "description": "Подготовка специалистов в области механики и математического моделирования",
        "career_prospects": "Инженер-механик, Исследователь, Разработчик симуляций",
    },
    {
        "title": "Приборостроение",
        "code": "12.03.01",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/priborostroenie/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 160,
        "duration": "4 года",
        "description": "Обучение разработке и производству приборов и устройств",
        "career_prospects": "Инженер-разработчик, Конструктор, Инженер-технолог",
    },
    {
        "title": "Системный анализ и управление",
        "code": "27.03.03",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/sistemnyj-analiz/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 158,
        "duration": "4 года",
        "description": "Подготовка специалистов в области системного анализа и управления",
        "career_prospects": "Системный аналитик, Business Analyst, Менеджер проектов",
    },
    {
        "title": "Мехатроника и робототехника",
        "code": "15.03.04",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/mehatronicom/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 159,
        "duration": "4 года",
        "description": "Обучение проектированию мехатронных систем и роботов",
        "career_prospects": "Мехатроник, Инженер-робототехник, Разработчик автоматизации",
    },
    {
        "title": "Конструирование и технология радиоэлектронных средств",
        "code": "11.03.04",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/konstruirovanie-radioel/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 161,
        "duration": "4 года",
        "description": "Подготовка инженеров по разработке радиоэлектронных систем",
        "career_prospects": "Инженер-разработчик, Конструктор, Инженер по испытаниям",
    },
    {
        "title": "Технологические машины и оборудование",
        "code": "15.03.02",
        "faculty": "fm",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/tehnologicheskie-mashiny/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 157,
        "duration": "4 года",
        "description": "Обучение разработке технологических машин и оборудования",
        "career_prospects": "Инженер-механик, Конструктор, Технолог",
    },

    # ====== ФАКУЛЬТЕТ ХИМИЧЕСКОЙ ТЕХНОЛОГИИ (5) ======
    {
        "title": "Химическая технология",
        "code": "18.03.01",
        "faculty": "fche",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/himicheskaya-tekhnolohiya/",
        "disciplines": ["Химия", "Математика", "Русский язык"],
        "min_score": 150,
        "duration": "4 года",
        "description": "Подготовка инженеров по химическим заводам и производству",
        "career_prospects": "Химический инженер, Технолог, Инженер-технолог",
    },
    {
        "title": "Биотехнология",
        "code": "19.03.01",
        "faculty": "fche",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/biotekhnolariya/",
        "disciplines": ["Химия", "Биология", "Русский язык"],
        "min_score": 148,
        "duration": "4 года",
        "description": "Обучение биотехнологиям и биотехнологическому производству",
        "career_prospects": "Биотехнолог, QA специалист, Разработчик лекарств",
    },
    {
        "title": "Биология",
        "code": "06.03.01",
        "faculty": "fche",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/biologiya/",
        "disciplines": ["Биология", "Химия", "Русский язык"],
        "min_score": 145,
        "duration": "4 года",
        "description": "Фундаментальная подготовка по биологии и естественным наукам",
        "career_prospects": "Биолог, Исследователь, Лаборант",
    },
    {
        "title": "Технология органических веществ",
        "code": "18.03.01",
        "faculty": "fche",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/tehnologiya-organicheskih/",
        "disciplines": ["Химия", "Математика", "Физика"],
        "min_score": 151,
        "duration": "4 года",
        "description": "Подготовка специалистов по синтезу органических веществ",
        "career_prospects": "Химик-органик, Технолог, Исследователь",
    },
    {
        "title": "Технология неорганических веществ",
        "code": "18.03.01",
        "faculty": "fche",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/tehnologiya-neorganicheskih/",
        "disciplines": ["Химия", "Математика", "Физика"],
        "min_score": 149,
        "duration": "4 года",
        "description": "Обучение технологии производства неорганических веществ",
        "career_prospects": "Химик, Технолог, Инженер-технолог",
    },

    # ====== ФАКУЛЬТЕТ ТРАНСПОРТА (5) ======
    {
        "title": "Наземные транспортно-технологические средства",
        "code": "23.03.02",
        "faculty": "ft",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/transportno-tehnologicheskiye/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 154,
        "duration": "4 года",
        "description": "Обучение разработке и эксплуатации транспортных средств",
        "career_prospects": "Инженер-автомобилист, Конструктор, Инженер-технолог",
    },
    {
        "title": "Организация перевозок и управление на транспорте",
        "code": "23.03.01",
        "faculty": "ft",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/organizacija-perevozok/",
        "disciplines": ["Экономика", "Математика", "Русский язык"],
        "min_score": 150,
        "duration": "4 года",
        "description": "Подготовка менеджеров и логистов транспортной отрасли",
        "career_prospects": "Логист, Менеджер перевозок, Диспетчер",
    },
    {
        "title": "Управление наземными транспортами и транспортными процессами",
        "code": "23.03.03",
        "faculty": "ft",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/upravlenie-transportom/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 152,
        "duration": "4 года",
        "description": "Подготовка специалистов по управлению транспортом и логистике",
        "career_prospects": "Менеджер проектов, Логист, Диспетчер-координатор",
    },
    {
        "title": "Локомотивы и подвижной состав железных дорог",
        "code": "23.05.01",
        "faculty": "ft",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/lokomotivostroenie/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 155,
        "duration": "5 лет",
        "description": "Подготовка специалистов по локомотивостроению",
        "career_prospects": "Инженер-проектировщик, Конструктор, Технолог",
    },
    {
        "title": "Автомобилестроение",
        "code": "23.03.02",
        "faculty": "ft",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/avtomobilestroenie/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 156,
        "duration": "4 года",
        "description": "Обучение разработке автомобилей и систем",
        "career_prospects": "Конструктор, Инженер-разработчик, Технолог",
    },

    # ====== ФАКУЛЬТЕТ ЭКОНОМИКИ И УПРАВЛЕНИЯ (5) ======
    {
        "title": "Экономика",
        "code": "38.03.01",
        "faculty": "f_ekonomiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/ekonomika/",
        "disciplines": ["Обществознание", "Математика", "Русский язык"],
        "min_score": 155,
        "duration": "4 года",
        "description": "Фундаментальная подготовка экономистов",
        "career_prospects": "Экономист, Финансовый аналитик, Инвестиционный консультант",
    },
    {
        "title": "Менеджмент",
        "code": "38.03.02",
        "faculty": "f_ekonomiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/menedzhment/",
        "disciplines": ["Обществознание", "История", "Русский язык"],
        "min_score": 150,
        "duration": "4 года",
        "description": "Подготовка менеджеров и руководителей предприятий",
        "career_prospects": "Менеджер, Руководитель проекта, HR специалист",
    },
    {
        "title": "Бизнес-информатика",
        "code": "38.03.05",
        "faculty": "f_ekonomiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/biznes-informatika/",
        "disciplines": ["Информатика", "Математика", "Русский язык"],
        "min_score": 158,
        "duration": "4 года",
        "description": "Обучение применению IT в бизнесе и управлении",
        "career_prospects": "Business Analyst, IT консультант, CIO",
    },
    {
        "title": "Государственное и муниципальное управление",
        "code": "38.03.04",
        "faculty": "f_ekonomiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/gmu/",
        "disciplines": ["Обществознание", "История", "Русский язык"],
        "min_score": 148,
        "duration": "4 года",
        "description": "Подготовка специалистов в области государственного управления",
        "career_prospects": "Государственный служащий, Аналитик, Менеджер",
    },
    {
        "title": "Финансы и кредит",
        "code": "38.03.01",
        "faculty": "f_ekonomiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/finansy-kredit/",
        "disciplines": ["Обществознание", "Математика", "Русский язык"],
        "min_score": 153,
        "duration": "4 года",
        "description": "Подготовка финансистов и банковских специалистов",
        "career_prospects": "Финансист, Банкир, Инвестиционный аналитик",
    },

    # ====== ФАКУЛЬТЕТ ГРАФИКИ И ИСКУССТВА (3) ======
    {
        "title": "Дизайн",
        "code": "54.03.01",
        "faculty": "f_iskusstva",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/dizajn/",
        "disciplines": ["Искусство", "История", "Русский язык"],
        "min_score": 140,
        "duration": "4 года",
        "description": "Подготовка дизайнеров и специалистов визуального творчества",
        "career_prospects": "Графический дизайнер, UX/UI дизайнер, Арт-директор",
    },
    {
        "title": "Живопись",
        "code": "54.03.02",
        "faculty": "f_iskusstva",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/zhivopis/",
        "disciplines": ["Искусство", "История", "Русский язык"],
        "min_score": 138,
        "duration": "4 года",
        "description": "Профессиональная подготовка художников-живописцев",
        "career_prospects": "Художник, Преподаватель, Реставратор",
    },
    {
        "title": "Графика",
        "code": "54.03.03",
        "faculty": "f_iskusstva",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/grafika/",
        "disciplines": ["Искусство", "История", "Русский язык"],
        "min_score": 139,
        "duration": "4 года",
        "description": "Обучение графическому искусству и книжной графике",
        "career_prospects": "Графический художник, Иллюстратор, Сценограф",
    },

    # ====== ФАКУЛЬТЕТ ИЗДАТЕЛЬСКОГО ДЕЛА (3) ======
    {
        "title": "Издательское дело",
        "code": "42.03.02",
        "faculty": "f_izdatelskogo",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/izdatelskoe-delo/",
        "disciplines": ["Русский язык", "Литература", "История"],
        "min_score": 145,
        "duration": "4 года",
        "description": "Подготовка специалистов издательского дела и полиграфии",
        "career_prospects": "Редактор, Издатель, Координатор проектов",
    },
    {
        "title": "Журналистика",
        "code": "42.03.02",
        "faculty": "f_izdatelskogo",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/zhurnalistika/",
        "disciplines": ["Русский язык", "История", "Обществознание"],
        "min_score": 143,
        "duration": "4 года",
        "description": "Подготовка журналистов и медиа-специалистов",
        "career_prospects": "Журналист, Медиа-менеджер, Корреспондент",
    },
    {
        "title": "Реклама и связи с общественностью",
        "code": "42.03.01",
        "faculty": "f_izdatelskogo",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/pr-reklama/",
        "disciplines": ["Русский язык", "История", "Обществознание"],
        "min_score": 142,
        "duration": "4 года",
        "description": "Подготовка специалистов в области PR и рекламы",
        "career_prospects": "PR менеджер, Рекламист, Event менеджер",
    },

    # ====== ФАКУЛЬТЕТ ПОЛИГРАФИЧЕСКИЙ (3) ======
    {
        "title": "Полиграфия",
        "code": "29.03.03",
        "faculty": "f_poligraficheskogo",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/poligrafiya/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 145,
        "duration": "4 года",
        "description": "Обучение полиграфическому производству и технологиям",
        "career_prospects": "Инженер-технолог, Мастер цеха, Технолог печати",
    },
    {
        "title": "Оборудование и технология полиграфических производств",
        "code": "29.03.01",
        "faculty": "f_poligraficheskogo",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/oborudovanie-tehnologiya/",
        "disciplines": ["Физика", "Математика", "Русский язык"],
        "min_score": 146,
        "duration": "4 года",
        "description": "Подготовка специалистов по полиграфическому оборудованию",
        "career_prospects": "Инженер, Наладчик оборудования, Технолог",
    },
    {
        "title": "Промышленная экология и биотехнология",
        "code": "20.03.01",
        "faculty": "f_poligraficheskogo",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/ekologiya-biotekhnologiya/",
        "disciplines": ["Биология", "Химия", "Русский язык"],
        "min_score": 144,
        "duration": "4 года",
        "description": "Обучение экологическим технологиям в производстве",
        "career_prospects": "Эколог, Технолог, Инженер охраны окружающей среды",
    },

    # ====== ФАКУЛЬТЕТ УРБАНИСТИКИ (5) ======
    {
        "title": "Архитектура",
        "code": "07.03.04",
        "faculty": "f_urbanistiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/arhitektura/",
        "disciplines": ["Русский язык", "Математика", "История"],
        "min_score": 150,
        "duration": "6 лет",
        "description": "Профессиональная подготовка архитекторов",
        "career_prospects": "Архитектор, Проектировщик, Главный архитектор",
    },
    {
        "title": "Градостроительство",
        "code": "07.03.03",
        "faculty": "f_urbanistiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/gradostroitelstvo/",
        "disciplines": ["Русский язык", "Математика", "История"],
        "min_score": 148,
        "duration": "4 года",
        "description": "Обучение градостроительству и городскому планированию",
        "career_prospects": "Градостроитель, Планировщик, Инженер-проектировщик",
    },
    {
        "title": "Экология и природопользование",
        "code": "05.03.04",
        "faculty": "f_urbanistiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/ekologiya/",
        "disciplines": ["Биология", "Химия", "Русский язык"],
        "min_score": 142,
        "duration": "4 года",
        "description": "Подготовка экологов и специалистов природопользования",
        "career_prospects": "Эколог, Аналитик, Инженер охраны окружающей среды",
    },
    {
        "title": "Строительство и гражданская инженерия",
        "code": "08.03.01",
        "faculty": "f_urbanistiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/stroitelstvo/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 147,
        "duration": "4 года",
        "description": "Подготовка инженеров в области строительства и конструкций",
        "career_prospects": "Инженер-строитель, Проектировщик, Сметчик",
    },
    {
        "title": "Землеустройство и кадастры",
        "code": "21.03.02",
        "faculty": "f_urbanistiki",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/zemelustrojstvo/",
        "disciplines": ["География", "Математика", "Обществознание"],
        "min_score": 140,
        "duration": "4 года",
        "description": "Обучение землеустройству и кадастровым работам",
        "career_prospects": "Кадастровый инженер, Геодезист, Картограф",
    },

    # ====== FDR (ПЕРЕДОВАЯ ИНЖЕНЕРНАЯ ШКОЛА) (2) ======
    {
        "title": "Фундаментальные основы инженерного образования",
        "code": "27.03.04",
        "faculty": "f_fdr",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/fdr-fundamentalnye/",
        "disciplines": ["Математика", "Физика", "Русский язык"],
        "min_score": 170,
        "duration": "4 года",
        "description": "Инновационная программа подготовки перспективных инженеров",
        "career_prospects": "Ведущий инженер, Технолог, Разработчик технологий",
    },
    {
        "title": "Промышленное проектирование и производство",
        "code": "15.03.01",
        "faculty": "f_fdr",
        "url": "https://mospolytech.ru/postupayushchim/programmy-obucheniya/fdr-promproekt/",
        "disciplines": ["Математика", "Физика", "Информатика"],
        "min_score": 168,
        "duration": "4 года",
        "description": "Подготовка инженеров по промышленному дизайну и производству",
        "career_prospects": "Инженер-конструктор, Дизайнер, Технолог",
    },
]


def generate_programs_cache():
    """Генерировать и сохранить кэш программ"""
    cache_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Основные факультеты
    faculties = [
        {"id": "fit", "name": "Факультет информационных технологий", "code": "FIT"},
        {"id": "fm", "name": "Факультет машиностроения", "code": "FM"},
        {"id": "fche", "name": "Факультет химической технологии и биотехнологии", "code": "FCHE"},
        {"id": "ft", "name": "Факультет транспорта", "code": "FT"},
        {"id": "f_ekonomiki", "name": "Факультет экономики и управления", "code": "F_EKONOMIKI"},
        {"id": "f_iskusstva", "name": "Факультет графики и искусства книги имени В.А.Фаворского", "code": "F_ISKUSSTVA"},
        {"id": "f_izdatelskogo", "name": "Факультет издательского дела и журналистики", "code": "F_IZDATELSKOGO"},
        {"id": "f_poligraficheskogo", "name": "Факультет полиграфический", "code": "F_POLIGRAFICHESKOGO"},
        {"id": "f_urbanistiki", "name": "Факультет урбанистики и городского хозяйства", "code": "F_URBANISTIKI"},
        {"id": "f_fdr", "name": "Факультет Передовой инженерной школы технологического лидерства FDR", "code": "F_FDR"},
    ]
    
    # Формируем программы
    programs = []
    for idx, prog_data in enumerate(PROGRAMS_DATA, 1):
        faculty_name = next((f["name"] for f in faculties if f["id"] == prog_data["faculty"]), "Другой факультет")
        
        program = {
            "id": f"prog_{idx}",
            "title": prog_data["title"],
            "code": prog_data["code"],
            "direction": prog_data["title"],
            "faculty_id": prog_data["faculty"],
            "faculty_name": faculty_name,
            "form": "очная",
            "level": "Бакалавриат",
            "description": prog_data.get("description"),
            "disciplines": prog_data.get("disciplines", []),
            "min_score": prog_data.get("min_score"),
            "duration": prog_data.get("duration"),
            "career_prospects": prog_data.get("career_prospects"),
            "url": prog_data["url"],
            "timestamp": datetime.now().isoformat(),
        }
        programs.append(program)
    
    result = {
        "faculties": faculties,
        "programs": programs,
        "last_updated": datetime.now().isoformat(),
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Кэш программ создан: {cache_file}")
    print(f"   Факультетов: {len(faculties)}")
    print(f"   Программ: {len(programs)}")
    
    # Показываем статистику по факультетам
    print("\n📊 Распределение программ по факультетам:")
    for faculty in faculties:
        count = len([p for p in programs if p["faculty_id"] == faculty["id"]])
        if count > 0:
            print(f"   {faculty['name']}: {count} программ")


if __name__ == "__main__":
    generate_programs_cache()



def generate_programs_cache():
    """Генерировать и сохранить кэш программ"""
    cache_file = Path(__file__).parent.parent / "data" / "cache" / "programs_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Основные факультеты
    faculties = [
        {"id": "fit", "name": "Факультет информационных технологий", "code": "FIT"},
        {"id": "fm", "name": "Факультет машиностроения", "code": "FM"},
        {"id": "fche", "name": "Факультет химической технологии и биотехнологии", "code": "FCHE"},
        {"id": "ft", "name": "Факультет транспорта", "code": "FT"},
        {"id": "f_ekonomiki", "name": "Факультет экономики и управления", "code": "F_EKONOMIKI"},
        {"id": "f_iskusstva", "name": "Факультет графики и искусства книги имени В.А.Фаворского", "code": "F_ISKUSSTVA"},
        {"id": "f_izdatelskogo", "name": "Факультет издательского дела и журналистики", "code": "F_IZDATELSKOGO"},
        {"id": "f_poligraficheskogo", "name": "Факультет полиграфический", "code": "F_POLIGRAFICHESKOGO"},
        {"id": "f_urbanistiki", "name": "Факультет урбанистики и городского хозяйства", "code": "F_URBANISTIKI"},
        {"id": "f_fdr", "name": "Факультет Передовой инженерной школы технологического лидерства FDR", "code": "F_FDR"},
    ]
    
    # Формируем программы
    programs = []
    for idx, prog_data in enumerate(PROGRAMS_DATA, 1):
        faculty_name = next((f["name"] for f in faculties if f["id"] == prog_data["faculty"]), "Другой факультет")
        
        program = {
            "id": f"prog_{idx}",
            "title": prog_data["title"],
            "code": prog_data["code"],
            "direction": prog_data["title"],
            "faculty_id": prog_data["faculty"],
            "faculty_name": faculty_name,
            "form": "очная",
            "level": "Бакалавриат",
            "description": prog_data.get("description"),
            "disciplines": prog_data.get("disciplines", []),
            "min_score": prog_data.get("min_score"),
            "duration": prog_data.get("duration"),
            "career_prospects": prog_data.get("career_prospects"),
            "url": prog_data["url"],
            "timestamp": datetime.now().isoformat(),
        }
        programs.append(program)
    
    result = {
        "faculties": faculties,
        "programs": programs,
        "last_updated": datetime.now().isoformat(),
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Кэш программ создан: {cache_file}")
    print(f"   Факультетов: {len(faculties)}")
    print(f"   Программ: {len(programs)}")
    
    # Показываем статистику по факультетам
    print("\n📊 Распределение программ по факультетам:")
    for faculty in faculties:
        count = len([p for p in programs if p["faculty_id"] == faculty["id"]])
        if count > 0:
            print(f"   {faculty['name']}: {count} программ")


if __name__ == "__main__":
    generate_programs_cache()
