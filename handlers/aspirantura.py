"""
Обработчики для раздела "Аспирантура" - единый модуль
Аналог mfc_services.py для страницы аспирантуры
"""

import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from utils.logger import logger
from handlers.navigation import get_student_menu_keyboard

router = Router()

# Загрузка данных аспирантуры из JSON
ASPIRANTURA_DATA_PATH = Path(__file__).parent.parent / "docs" / "aspirantura_data.json"

def load_aspirantura_data():
    """Загрузка данных аспирантуры из JSON"""
    try:
        with open(ASPIRANTURA_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("✅ Данные аспирантуры успешно загружены")
        return data
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных аспирантуры: {e}")
        return None

# Глобальная переменная для хранения данных
aspirantura_data = None

async def init_aspirantura_data():
    """Инициализация данных аспирантуры"""
    global aspirantura_data
    aspirantura_data = load_aspirantura_data()

# ============= ДАННЫЕ ПО УМОЛЧАНИЮ (HTML-страница) =============
DEFAULT_DATA = {
    "title": "Подготовка научно-педагогических работников",
    "description": "Аспирантура — основная форма подготовки научно-педагогических кадров, предоставляющая возможность повышения уровня образования, научной и педагогической квалификации.",
    "hero_image": "/upload/iblock/eb5/science_1.jpg",
    
    "info_blocks": [
        {
            "title": "Вы – аспирант",
            "content": "Обучение в аспирантуре является важной ступенью в подготовке научно-квалификационной работы (диссертации).\n\nДля успешного освоения образовательной программы и полноценного взаимодействия с подразделениями вуза аспиранту Московского Политеха предоставляется доступ к личному кабинету."
        },
        {
            "title": "Учебная и научная база",
            "content": "В процессе обучения аспирант, в том числе, пользуется материально-технической базой факультета/института, учебно-методической и научной поддержкой кафедры, электронно-библиотечными ресурсами университета."
        },
        {
            "title": "Практика",
            "content": "Осваивая образовательную программу, аспирант получает компетенции по научно-исследовательской и педагогической деятельности. Пройдя практику в подразделениях университета и организациях индустриальных партнеров, аспирант приобретает навыки, необходимые для дальнейшего карьерного роста."
        },
        {
            "title": "Научные исследования аспиранта",
            "content": "Обязательным условием осуществления аспирантом научных исследований является публикация результатов своей научно-исследовательской деятельности в изданиях, входящих в рецензируемый перечень ВАК.\n\nА также апробация результатов на российских и международных конференциях, конкурсах и форумах.\n\nТакже аспирант имеет возможность участвовать в научных проектах, конкурсах на получение гранта, оформлять патенты и свидетельства на полезную модель."
        },
        {
            "title": "Промежуточная аттестация аспиранта",
            "content": "Обязательной промежуточной формой отчетности аспиранта является аттестация по выполнению индивидуального плана аспиранта и научных исследований."
        }
    ],
    
    "contacts": {
        "schedule": {
            "title": "Часы работы",
            "hours": [
                {"days": "Пн. — Чт.", "time": "9:30 — 18:30"},
                {"days": "Пт.", "time": "9:30 — 17:15"},
                {"days": "Сб. — Вс.", "time": "выходные"},
                {"days": "Перерыв", "time": "13:00 - 13:45"}
            ]
        },
        "email": {
            "title": "E-mail",
            "address": "aspirant@mospolytech.ru"
        },
        "phone": {
            "title": "Телефон для связи",
            "contacts": [
                "Начальник Центра подготовки кадров высшей квалификации Дикова Елена Викторовна: +7 (495) 223-05-23 доб. 1384",
                "+7 (495) 223-05-23 доб. 1294",
                "Ведущий инженер Ситникова Татьяна Анатольевна"
            ]
        },
        "address": {
            "title": "Адрес",
            "text": "107023, г. Москва, ул. Большая Семёновская, 38, кабинет Б-301 (корпус Б, 3-й этаж)",
            "map_link": "https://mospolytech.ru/ob-universitete/adresa-i-kontakty/"
        }
    },
    
    "faq": [
        {
            "question": "Когда сдавать кандидатские экзамены?",
            "answer": "Кандидатские экзамены являются формой промежуточной аттестации и сдаются в соответствии с графиком учебного процесса и расписанием."
        },
        {
            "question": "Какие кандидатские экзамены можно сдать?",
            "answer": "В перечень кандидатских экзаменов входят: история и философия науки, иностранный язык, специальная дисциплина в соответствии с темой диссертации на соискание ученой степени кандидата наук."
        },
        {
            "question": "Когда утверждается научный руководитель и тема диссертации?",
            "answer": "Не позднее 3-х месяцев с начала учебного года приказом ректора на основании решения Ученого совета Университета, обучающемуся назначается научный руководитель, а также утверждается тема научно-исследовательской работы и диссертации."
        },
        {
            "question": "Где получить справку аспиранта?",
            "answer": "Все справки можно заказать и получить в отделениях центра по работе со студентами. Аспирантское удостоверение и зачетку получают там же."
        },
        {
            "question": "Где узнать расписание занятий?",
            "answer": "Расписание размещено в личном кабинете, а также на сайте в разделе Расписания."
        }
    ],
    
    "quick_links": [
        {
            "title": "Прием в аспирантуру",
            "url": "https://mospolytech.ru/postupayushchim/priem-v-universitet/pravila-priema/",
            "color": "purple"
        },
        {
            "title": "Личный кабинет",
            "url": "https://e.mospolytech.ru/",
            "color": "blue"
        },
        {
            "title": "Расписание занятий",
            "url": "https://mospolytech.ru/obuchauschimsya/raspisaniya/",
            "color": "black"
        },
        {
            "title": "Прикрепление экстерном",
            "url": "https://mospolytech.ru/upload/files/aspirantura/prikreplenie-ehksternov-k-Moskow-Poly-dlya-sdachi-kandidatskikh-ehkzamenov.pdf",
            "color": "green",
            "description": "для сдачи кандидатского минимума"
        }
    ]
}

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_data():
    """Получение данных аспирантуры"""
    if aspirantura_data:
        return aspirantura_data
    return DEFAULT_DATA

def get_info_blocks():
    """Получение блоков информации об обучении"""
    return get_data().get("info_blocks", [])

def get_faq_list():
    """Получение списка FAQ"""
    return get_data().get("faq", [])

def get_quick_links():
    """Получение быстрых ссылок"""
    return get_data().get("quick_links", [])

def get_contacts():
    """Получение контактной информации"""
    return get_data().get("contacts", {})

def format_info_blocks():
    """Форматирование блоков информации об обучении"""
    blocks = get_info_blocks()
    text = "📖 **Обучение в аспирантуре**\n\n"
    
    for i, block in enumerate(blocks, 1):
        text += f"*{i}. {block['title']}*\n"
        text += f"{block['content']}\n\n"
    
    return text

def format_contacts():
    """Форматирование контактной информации"""
    contacts = get_contacts()
    text = "📞 **Контактная информация**\n\n"
    
    # Режим работы
    schedule = contacts.get("schedule", {})
    if schedule:
        text += f"🕐 *{schedule.get('title', 'Часы работы')}*\n"
        for item in schedule.get("hours", []):
            text += f"• {item.get('days', '')}: {item.get('time', '')}\n"
        text += "\n"
    
    # Email
    email = contacts.get("email", {})
    if email:
        text += f"📧 *{email.get('title', 'E-mail')}*\n"
        text += f"`{email.get('address', '')}`\n\n"
    
    # Телефоны
    phone = contacts.get("phone", {})
    if phone:
        text += f"📱 *{phone.get('title', 'Телефон для связи')}*\n"
        for contact in phone.get("contacts", []):
            text += f"• {contact}\n"
        text += "\n"
    
    # Адрес
    address = contacts.get("address", {})
    if address:
        text += f"📍 *{address.get('title', 'Адрес')}*\n"
        text += f"{address.get('text', '')}\n"
    
    return text

def format_faq():
    """Форматирование FAQ"""
    faq_list = get_faq_list()
    if not faq_list:
        return "❓ Вопросы временно недоступны"
    
    text = "❓ **Часто задаваемые вопросы**\n\n"
    for i, item in enumerate(faq_list, 1):
        text += f"*{i}. {item['question']}*\n"
        text += f"_{item['answer']}_\n\n"
    
    return text

def get_main_keyboard():
    """Создание главной клавиатуры для раздела аспирантуры"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Обучение в аспирантуре", callback_data="asp_info")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="asp_contacts")],
        [InlineKeyboardButton(text="❓ Часто задаваемые вопросы", callback_data="asp_faq")],
        [InlineKeyboardButton(text="🔗 Полезные ссылки", callback_data="asp_links")],
        [InlineKeyboardButton(text="📋 Прием в аспирантуру", callback_data="asp_admission")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="asp_back_to_menu")],
    ])
    return keyboard

def get_links_keyboard():
    """Создание клавиатуры с быстрыми ссылками"""
    links = get_quick_links()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for link in links:
        btn = InlineKeyboardButton(
            text=link["title"],
            url=link["url"]
        )
        keyboard.inline_keyboard.append([btn])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="asp_back_to_main")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 В раздел студента", callback_data="asp_back_to_menu")
    ])
    
    return keyboard

def get_back_to_main_keyboard():
    """Клавиатура для возврата в главное меню аспирантуры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="asp_back_to_main")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="asp_back_to_menu")],
    ])

# ============= ОСНОВНОЙ ОБРАБОТЧИК =============

@router.message(F.text == "🎓 Аспирантура")
async def handle_aspirantura(message: types.Message):
    """Обработчик для раздела аспирантуры"""
    if not aspirantura_data:
        await init_aspirantura_data()
    
    data = get_data()
    
    text = f"🎓 **{data.get('title', 'Аспирантура')}**\n\n"
    text += f"{data.get('description', '')}\n\n"
    text += "Выбери интересующий раздел:"
    
    keyboard = get_main_keyboard()
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# ============= ОБРАБОТЧИКИ КНОПОК =============

@router.callback_query(F.data == "asp_info")
async def handle_asp_info(callback: types.CallbackQuery):
    """Обработчик - информация об обучении"""
    text = format_info_blocks()
    keyboard = get_back_to_main_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_contacts")
async def handle_asp_contacts(callback: types.CallbackQuery):
    """Обработчик - контактная информация"""
    text = format_contacts()
    keyboard = get_back_to_main_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_faq")
async def handle_asp_faq(callback: types.CallbackQuery):
    """Обработчик - FAQ"""
    text = format_faq()
    keyboard = get_back_to_main_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_links")
async def handle_asp_links(callback: types.CallbackQuery):
    """Обработчик - полезные ссылки"""
    text = "🔗 **Полезные ссылки**\n\nВыбери нужный раздел:"
    keyboard = get_links_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_admission")
async def handle_asp_admission(callback: types.CallbackQuery):
    """Обработчик - прием в аспирантуру"""
    text = "📋 **Прием в аспирантуру**\n\n"
    text += "Подробная информация о правилах приема, сроках подачи документов "
    text += "и вступительных испытаниях доступна на официальном сайте.\n\n"
    text += "🔗 [Перейти на страницу приема](https://mospolytech.ru/postupayushchim/priem-v-universitet/pravila-priema/)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть страницу приема", url="https://mospolytech.ru/postupayushchim/priem-v-universitet/pravila-priema/")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="asp_back_to_main")],
        [InlineKeyboardButton(text="🔙 В раздел студента", callback_data="asp_back_to_menu")],
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_back_to_main")
async def handle_asp_back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню аспирантуры"""
    data = get_data()
    
    text = f"🎓 **{data.get('title', 'Аспирантура')}**\n\n"
    text += f"{data.get('description', '')}\n\n"
    text += "Выбери интересующий раздел:"
    
    keyboard = get_main_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_back_to_menu")
async def handle_asp_back_to_menu(callback: types.CallbackQuery):
    """Возврат в раздел студента"""
    student_text = "📚 **Информация для студентов**\n\nЗдесь ты найдешь всё что нужно для учёбы и жизни в университете.\n\nВыбери интересующий раздел:"
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(student_text, reply_markup=get_student_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

# ============= ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ =============

@router.callback_query(F.data == "asp_individual_plan")
async def handle_individual_plan(callback: types.CallbackQuery):
    """Информация об индивидуальном плане аспиранта"""
    text = "📋 **Индивидуальный план аспиранта**\n\n"
    text += "Индивидуальный план - это основной документ, определяющий содержание и организацию обучения аспиранта.\n\n"
    text += "Он включает:\n"
    text += "• План учебных занятий\n"
    text += "• План научных исследований\n"
    text += "• Сроки сдачи кандидатских экзаменов\n"
    text += "• План подготовки диссертации\n\n"
    text += "Индивидуальный план утверждается научным руководителем и руководителем образовательной программы."
    
    keyboard = get_back_to_main_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()

@router.callback_query(F.data == "asp_scholarship")
async def handle_scholarship_info(callback: types.CallbackQuery):
    """Информация о стипендиях для аспирантов"""
    text = "💰 **Стипендии для аспирантов**\n\n"
    text += "Аспиранты Московского Политеха имеют право на следующие виды стипендий:\n\n"
    text += "• **Государственная академическая стипендия** - выплачивается всем аспирантам, обучающимся на бюджете\n"
    text += "• **Повышенная стипендия** - за особые достижения в научной деятельности\n"
    text += "• **Именные стипендии** - Президента РФ, Правительства РФ, мэра Москвы\n"
    text += "• **Стипендии Президента РФ** - для молодых ученых и аспирантов\n\n"
    text += "Подробную информацию можно получить в Многофункциональном центре."
    
    keyboard = get_back_to_main_keyboard()
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    await callback.answer()
