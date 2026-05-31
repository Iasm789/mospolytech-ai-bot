"""
Обработчики для раздела контакты Московского Политеха
"""

from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.navigation import get_main_menu_keyboard, BACK_TEXT

router = Router()


class ContactsForm(StatesGroup):
    """Состояния для раздела контакты"""
    viewing_contacts = State()


def get_contacts_keyboard():
    """Клавиатура раздела контакты"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏛️ Главный корпус"), KeyboardButton(text="📞 Приёмная комиссия")],
            [KeyboardButton(text="📰 Пресс-служба"), KeyboardButton(text="🎯 Целевое обучение")],
            [KeyboardButton(text="🏢 МФЦ"), KeyboardButton(text="📚 Библиотека")],
            [KeyboardButton(text="📋 Все адреса корпусов")],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True
    )


@router.message(F.text == "📞 Контакты")
async def show_contacts_menu(message: types.Message, state: FSMContext):
    """Показать меню контактов"""
    await state.set_state(ContactsForm.viewing_contacts)
    
    contacts_text = """
📞 Контакты Московского Политеха

Здесь ты найдёшь все необходимые контакты для связи с различными подразделениями университета.

Выбери нужный раздел:
"""
    
    await message.answer(
        contacts_text,
        reply_markup=get_contacts_keyboard()
    )


@router.message(ContactsForm.viewing_contacts, F.text == "🏛️ Главный корпус")
async def show_main_building(message: types.Message):
    """Показать информацию о главном корпусе"""
    contacts_text = """
🏛️ ГЛАВНЫЙ КОРПУС

📍 Адрес:
107023, Москва
Большая Семёновская, 38

📞 Телефоны:
+7 (495) 223-05-23
+7 (495) 276-37-36

🕒 Часы работы:
ПН-ПТ: 9:00-20:00
СБ-ВС: выходные

📧 Электронная почта (общие вопросы):
mospolytech@mospolytech.ru

🌐 Сайт: www.mospolytech.ru
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())


@router.message(ContactsForm.viewing_contacts, F.text == "📞 Приёмная комиссия")
async def show_admission_contacts(message: types.Message):
    """Показать контакты приёмной комиссии"""
    contacts_text = """
📞 ПРИЕМНАЯ КОМИССИЯ
Прием документов

📞 Телефоны:
+7 (495) 223-05-23
+7 (800) 550-91-42

🕒 Часы работы:
ПН-ЧТ: 10:30-18:00
ПТ: 10:30-17:00
СБ-ВС: Выходной

📧 По документам и вопросам:
priem@mospolytech.ru

🌐 Сайт приёмной комиссии:
priem.mospolytech.ru
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())


@router.message(ContactsForm.viewing_contacts, F.text == "📰 Пресс-служба")
async def show_press_service(message: types.Message):
    """Показать контакты пресс-службы"""
    contacts_text = """
📰 ПРЕСС-СЛУЖБА

📞 Телефон:
+7 (495) 223-05-23

📧 Обратная связь по сайту:
media@mospolytech.ru

📧 СМИ и новости:
press@mospolytech.ru

Соцсети университета:
• Telegram: @mospolytech
• ВКонтакте: vk.com/mospolytech
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())


@router.message(ContactsForm.viewing_contacts, F.text == "🎯 Целевое обучение")
async def show_target_training(message: types.Message):
    """Показать информацию о целевом обучении"""
    contacts_text = """
🎯 ЦЕЛЕВОЕ ОБУЧЕНИЕ

📞 Единый контакт-центр «Приём в вуз»:
• Россия: +7 (800) 301-44-55
• Зарубеж: +7 (495) 122-22-68

Контактные лица:

👩‍💼 Синица Александра Евгеньевна
📞 +7 (495) 223-05-23 (доб. 1618)
📧 a.e.sinica@mospolytech.ru

👨‍💼 Сологуб Никита Дмитриевич
📞 +7 (495) 223-05-23 (доб. 1617)
📧 n.d.sologub@mospolytech.ru

📌 Памятка абитуриенту:
https://mospolytech.ru/abiturientam/tselevoe-obuchenie/
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())


@router.message(ContactsForm.viewing_contacts, F.text == "🏢 МФЦ")
async def show_mfc(message: types.Message):
    """Показать информацию о МФЦ"""
    contacts_text = """
🏢 МНОГОФУНКЦИОНАЛЬНЫЙ ЦЕНТР (МФЦ)
Услуги обучающимся, работникам и ранее обучавшимся

📞 Телефон:
+7 (495) 223-05-23

📍 Отделения МФЦ:
• Большая Семёновская, 38
• Павла Корчагина, 22
• Автозаводская, 16
• Прянишникова, 2А

🕒 Часы работы отделений:
ПН-ПТ: 10:00-18:00
СБ-ВС: выходные

📧 Email: mfc@mospolytech.ru

Услуги МФЦ:
• Справки об обучении
• Восстановление студенческого билета
• Договоры на обучение
• Документы об образовании
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())


@router.message(ContactsForm.viewing_contacts, F.text == "📋 Все адреса корпусов")
async def show_all_addresses(message: types.Message):
    """Показать все адреса корпусов"""
    contacts_text = """
📋 ВСЕ АДРЕСА КОРПУСОВ МОСКОВСКОГО ПОЛИТЕХА

🏛️ Главный корпус:
Большая Семёновская, 38

🏢 Корпус на Павла Корчагина:
ул. Павла Корчагина, 22

🏭 Корпус на Автозаводской:
ул. Автозаводская, 16

🏫 Корпус на Прянишникова:
ул. Прянишникова, 2А

🔧 Корпус на Михалковской:
ул. Михалковская, 7

⚙️ Корпус на Б. Семеновской (мастерские):
Большая Семёновская, 38, стр. 4

🌿 Корпус в Текстильщиках:
ул. 8-я Текстильщиков, 14

🔬 Лабораторный корпус:
проезд Энтузиастов, 36

📞 Единый справочный телефон:
+7 (495) 223-05-23
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())

@router.message(ContactsForm.viewing_contacts, F.text == "📚 Библиотека")
async def show_library(message: types.Message):
    """Показать информацию о библиотеках"""
    contacts_text = """
📚 БИБЛИОТЕКИ МОСКОВСКОГО ПОЛИТЕХА

ГРАФИК РАБОТЫ И КОНТАКТЫ:

Основная библиотека:
Понедельник – четверг: 10:00 - 20:00
Пятница: 10:00 - 18:00
Суббота, воскресенье – выходные дни
Последняя пятница каждого месяца — санитарный день

Новая библиотека:
Понедельник – пятница: 10:00 - 22:00
Суббота, воскресенье – выходные дни

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

БИБЛИОТЕКА НА АВТОЗАВОДСКОЙ

Адрес: г. Москва, ул. Автозаводская, 16, корп. 2, ауд. 2702, 2706
Телефон: +7 (495) 223-05-23, доб. 2270

Для обучающихся:
• Транспортного факультета
• Факультета машиностроения
• Факультета урбанистики и городского хозяйства
• Факультета химической технологии и биотехнологии
• Факультета издательского дела и журналистики
• Передовой инженерной школы технологического лидерства «FDR»

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

БИБЛИОТЕКА НА КОРЧАГИНА

Адрес: г. Москва, ул. П. Корчагина, 22, ауд. 114
Телефон: +7 (495) 223-05-23, доб. 3210

Для обучающихся:
• Факультета экономики и управления

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

БИБЛИОТЕКА НА ПРЯНИШНИКОВА

Адрес: г. Москва, ул. Прянишникова, 2а, 7 этаж
Телефон: +7 (495) 223-05-23, доб. 4106

Для обучающихся:
• Института графики и искусства книги имени В.А. Фаворского
• Полиграфического факультета
• Факультета информационных технологий
• Факультет экономики и управления (реклама и связи с общественностью)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

НОВАЯ БИБЛИОТЕКА

Адреса:
• г. Москва, ул. Большая Семеновская, 38 (ауд. Н-416)
• г. Москва, ул. Автозаводская, 16 (ауд. 4905)

КОНТАКТНЫЕ ДАННЫЕ:

И.о. начальника: Гафурова Наталья Матвеевна,
заслуженный работник культуры РФ

Телефон: +7 (495) 223-05-23, доб. 4081
E-mail: library@mospolytech.ru
"""
    
    await message.answer(contacts_text, reply_markup=get_contacts_keyboard())

@router.message(ContactsForm.viewing_contacts, F.text == "◀️ Назад в главное меню")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    await message.answer(
        "📋 Главное меню",
        reply_markup=get_main_menu_keyboard()
    )