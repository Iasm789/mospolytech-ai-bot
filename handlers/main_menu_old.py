"""
Обработчики главного меню и навигации (оптимизированная версия)
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from utils.logger import logger
from handlers.navigation import (
    get_main_menu_keyboard,
    get_aspirant_menu_keyboard,
    get_student_menu_keyboard,
    SECTIONS,
    BACK_TEXT
)

router = Router()



@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name or "Друг"
    
    welcome_text = f"👋 Привет, {user_name}!\n\nЧто тебе нужно?"
    
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Обработчик команды /menu"""
    await message.answer(
        "📋 Главное меню",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = "/start - заново\n/menu - меню\n\nВыбери нужный раздел в меню ↓"
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.message(F.text == "👨‍🎓 Абитуриенту")
async def handle_aspirant(message: types.Message):
    """Обработчик для абитуриентов"""
    aspirant_text = "👨‍🎓 Интересующий раздел:"
    
    await message.answer(aspirant_text, reply_markup=get_aspirant_menu_keyboard())



@router.message(F.text == "📚 Направления обучения")
async def handle_directions(message: types.Message):
    """Информация о направлениях обучения"""
    directions_text = """
📚 **Основные направления обучения в МосПолитехе:**

🖥️ **Информатика и вычислительная техника**
   • Программирование и разработка ПО
   • Искусственный интеллект и машинное обучение
   • Системное администрирование

⚙️ **Техника и технология**
   • Механическая инженерия
   • Энергетика и теплотехника
   • Материаловедение

💼 **Экономика и управление**
   • Менеджмент
   • Экономика предприятия
   • Финансовый анализ

🎨 **Искусство и дизайн**
   • Графический дизайн
   • Веб-дизайн
   • Интерактивные технологии

📖 **Прочие программы**
   • Полный список на сайте: https://mospolytech.ru/programs

Средний балл для поступления: 70-85 (по ЕГЭ)
Все программы аккредитованы и признаны на международном уровне!
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад к абитуриенту")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(directions_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "📋 Процесс поступления")
async def handle_admission_process(message: types.Message):
    """Информация о процессе поступления"""
    process_text = """
📋 **Этапы поступления в МосПолитех:**

**1️⃣ Подготовка документов**
   • Заявление о поступлении
   • Паспорт и копия
   • Документ об образовании (аттестат)
   • 4 фотографии 3×4 см
   • Результаты ЕГЭ

**2️⃣ Подача документов**
   • Сроки подачи: с июля по август
   • Личное посещение или по почте
   • Онлайн-подача через сайт университета

**3️⃣ Рассмотрение документов**
   • Проверка полноты и подлинности документов
   • Проверка оценок ЕГЭ
   • Формирование рейтинговых списков

**4️⃣ Зачисление**
   • Официальный приказ о зачисении
   • Уведомление абитуриента
   • Прохождение первичной регистрации

**5️⃣ Начало обучения**
   • Ознакомительное совещание
   • Получение студенческого билета
   • Начало занятий в сентябре

📅 Основные сроки 2026:
   • Прием документов: 5 июля - 25 августа
   • Зачисление: 27 августа
   • Начало семестра: 1 сентября
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад к абитуриенту")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(process_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "📞 Контакты приемной комиссии")
async def handle_admission_contacts(message: types.Message):
    """Контакты приемной комиссии"""
    contacts_text = """
📞 **Контакты приемной комиссии МосПолитеха:**

📍 **Главный офис**
   Ул. Большая Семеновская, д. 38
   Москва, 107023

📧 **Email:** abiturient@mospolytech.ru
📞 **Телефон:** +7 (495) 223-55-00
💬 **WhatsApp:** +7 (999) XXX-XX-XX

🕐 **Режим работы:**
   Пн-Пт: 09:00 - 18:00
   Сб: 10:00 - 16:00
   Вс: выходной

🌐 **Официальный сайт:**
   https://mospolytech.ru

📱 **Социальные сети:**
   VK: https://vk.com/mospolytech
   Instagram: @mospolytech_official
   Telegram: @mospolytech_news

💡 **Часто задаваемые вопросы:**
   https://mospolytech.ru/faq

Ждем твоих вопросов! 😊
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад к абитуриенту")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(contacts_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "◀️ Назад к абитуриенту")
async def back_to_aspirant(message: types.Message):
    """Вернуться к разделу абитуриентов"""
    await handle_aspirant(message)


@router.message(F.text == BACK_TEXT)
async def back_to_main_menu(message: types.Message):
    """Вернуться в главное меню из любого раздела"""
    await message.answer("📋 Главное меню", reply_markup=get_main_menu_keyboard())



@router.message(F.text == "📚 Студенту")
async def handle_student(message: types.Message):
    """Обработчик для студентов"""
    student_text = "📚 Выбери раздел, который нужен:"
    
    await message.answer(student_text, reply_markup=get_student_menu_keyboard())


@router.message(F.text == "❓ Помощь")
async def handle_help(message: types.Message):
    """Обработчик для помощи"""
    help_text = "❓ Выбери интересующую категорию:"
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 FAQ"), KeyboardButton(text="🛠️ Помощь")],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True
    )
    
    await message.answer(help_text, reply_markup=keyboard)


@router.message(F.text == "📚 Часто задаваемые вопросы")
async def handle_faq(message: types.Message):
    """Часто задаваемые вопросы"""
    faq_text = (
        "📚 **Частые вопросы:**\n\n"
        "❓ Как получить расписание?\n"
        "→ Студенту → Расписание, введи номер группы\n\n"
        "❓ Размер стипендии?\n"
        "→ Базовая 2,500₽, повышенная до 10,000₽\n\n"
        "❓ Справка для банка?\n"
        "→ Деканат или портал студента\n\n"
        "Больше на сайте: https://mospolytech.ru/faq"
    )
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text=BACK_TEXT)],
        ],
        resize_keyboard=True
    )
    
    await message.answer(faq_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "🎓 Вопросы об учёбе")
async def handle_study_questions(message: types.Message):
    """Вопросы об учёбе"""
    study_text = """
🎓 **Вопросы об учёбе:**

**Q: Обязательны ли все практические занятия?**
A: Да, посещаемость практик обязательна. При отсутствии требуется справка.

**Q: Какой процент пропуска допускается?**
A: Не более 20% за семестр. При превышении может быть отчисление.

**Q: Как пересдавать экзамен, если не сдал с первой попытки?**
A: 1️⃣ Пересдача назначается деканатом
   2️⃣ Возможная дополнительная плата
   3️⃣ Требуется согласие преподавателя

**Q: Можно ли взять кредит на доп. предметы?**
A: Да, максимум до 12 кредитов в семестр. Заявка через портал.

**Q: Как запросить индивидуальный график обучения?**
A: Обратись в деканат с документами. Возможно при наличии медицинских показаний.

**Q: Где найти описание всех курсов (syllabus)?**
A: На сайте университета в разделе "Курсы" или в портале студента.

**Q: Какие курсы связаны с моей специальностью?**
A: Смотри "План обучения" в портале студента или спроси у куратора.

**Q: Как повысить свой балл, если провалил экзамен?**
A: Переэкзаменовка, дополнительные задания от преподавателя, участие в проектах.

**Q: Когда результаты экзаменов выставляет преподаватель?**
A: Обычно в течение 5-7 дней после экзамена. Проверяй портал студента.

**Q: Как выглядит система оценок?**
A: От F (0-50%) до A (90-100%). Также используется балл по 100-балльной шкале.
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(study_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "🏫 Вопросы про расписание")
async def handle_schedule_questions(message: types.Message):
    """Вопросы про расписание"""
    schedule_text = """
🏫 **Часто задаваемые вопросы про расписание:**

**Q: Где найти своё расписание?**
A: В этом боте! Нажми "📚 Студенту" → "📅 Расписание" и введи номер группы.

**Q: Какие периоды я могу выбрать?**
A: Доступны следующие варианты:
   • 📅 На сегодня - только текущий день
   • 📆 На завтра - расписание на завтра
   • 📋 На эту неделю - 7 дней начиная с сегодня
   • 📋 На следующую неделю - расписание на 7 дней вперед
   • 📅 Выбрать дату - расписание на конкретную дату (формат ДД.MM)
   • 📋 На месяц - расписание на весь месяц

**Q: Как выбрать расписание на конкретную дату?**
A: Нажми "📅 Выбрать дату" и введи дату в формате ДД.MM (например, 28.02).

**Q: От чего зависит расписание?**
A: От программы обучения, номера группы, курса, факультета и периода (семестр).

**Q: Почему у нас иногда нет пар в определённые дни?**
A: Это может быть выходной день, каникулы или специальный учебный график.

**Q: Как узнать, в каком корпусе моя пара?**
A: В расписании указывается номер аудитории, по которому можно определить корпус.

**Q: Как быстро переключиться между разными периодами?**
A: После просмотра расписания ты можешь нажать:
   • "📅 На другую дату" - чтобы посмотреть расписание на другую дату (для той же группы)
   • "📋 На другой период" - чтобы выбрать другой временной период

**Q: Пара перенесена - где про это узнать?**
A: Объявления в чатах, рассылка от деканата, сайт университета и боте (будут обновления).

**Q: Когда начинаются занятия в день?**
A: Обычно в 08:30 первая пара, но могут быть исключения. Смотри расписание.

**Q: Сколько пар в день?**
A: Обычно 3-4 пары в день, может быть 5-6 в напряженные дни.

**Q: Как долго длится одна пара?**
A: 90 минут (1.5 часа). Между парами перемена 10-15 минут.

**Q: Мож ли я поменять время пары?**
A: Нет. Занятия в указанное время в расписании обязательны.

**Q: Где можно увидеть расписание на весь год?**
A: На портале студента, на сайте факультета или через мобильное приложение МосПолитеха.
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(schedule_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "💼 Вопросы о карьере")
async def handle_career_questions(message: types.Message):
    """Вопросы о карьере"""
    career_text = """
💼 **Вопросы о карьере и трудоустройстве:**

**Q: Как начать искать работу во время обучения?**
A: Подпишись на "Отдел трудоустройства", посещай ярмарки вакансий.
   Профиль на LinkedIn, резюме и портфолио проектов - вот с чего начать.

**Q: Какие компании приходят в университет?**
A: Google, Yandex, VK, Gazprom, Rostelecom, Sberbank и многие другие.

**Q: Как получить стажировку?**
A: На ярмарках вакансий, через портал "Карьера", рекомендации преподавателей.

**Q: Нужна ли практика после 2 или 3 курса?**
A: Желательна! Опыт работы важен для будущей карьеры. Обычно с 3 курса.

**Q: Сколько может быть часов подработки во время учёбы?**
A: Максимум 20 часов в неделю (по закону). Рекомендуется не более 10-15.

**Q: Как написать хорошее резюме?**
A: На портале "Карьера" есть шаблоны, или посещай мастер-классы HR.

**Q: Какая средняя зарплата выпускников?**
A: 150,000-250,000 руб. в зависимости от специальности и компании.

**Q: Где работают выпускники МосПолитеха?**
A: В IT, банках, консалтинге, энергетике, телекоме, государственных структурах.

**Q: Нужна ли мне программа обмена для карьеры?**
A: Нет обязательной необходимости, но она добавляет конкурентное преимущество.

**Q: Как найти наставника в компании?**
A: Программы менторства есть у многих работодателей. Спроси на ярмарке вакансий.
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(career_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "🛠️ Техническая поддержка")
async def handle_technical_support(message: types.Message):
    """Техническая поддержка"""
    tech_text = """
🛠️ **Техническая поддержка:**

**Проблемы с доступом в портал:**
📞 +7 (495) 223-55-00
📧 support@mospolytech.ru
🕐 Пн-Пт: 09:00-18:00

**Проблемы с приложением МосПолитеха:**
   ⚠️ Переустанови приложение
   ⚠️ Очисти кеш (Settings → Apps → МосПолитеха → Clear Cache)
   ⚠️ Проверь интернет соединение
   📧 app_support@mospolytech.ru

**Проблемы с электронной почтой университета:**
   📧 mail_support@mospolytech.ru
   📞 +7 (495) 223-55-11

**Проблемы с Wi-Fi в университете:**
   📱 Реги на https://wifi.mospolytech.ru
   📧 network_team@mospolytech.ru
   📞 +7 (495) 223-55-33

**Проблемы с камерой/микрофоном на онлайн-занятиях:**
   ✅ Проверь разрешения браузера
   ✅ Переустанови браузер
   ✅ Используй Chrome или Firefox
   📧 online_support@mospolytech.ru

**Проблемы с платежом за обучение:**
   💳 Отдел Финансов (Корпус 1, каб. 301)
   📧 finance@mospolytech.ru
   📞 +7 (495) 223-55-22

**Проблемы с данным ботом:**
   🤖 Напишите в поддержку Telegram: @mospolytech_support
   💬 Используйте кнопку "💬 Обратная связь"

**Время ответа:**
   ⚡ Email: 1-2 рабочих дня
   ☎️ Телефон: в рабочие часы
   💬 Чат: 30-60 минут

Мы помогаем круглосуточно! 🚀
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(tech_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "💬 Обратная связь")
async def handle_feedback(message: types.Message):
    """Обработчик для обратной связи"""
    feedback_text = """
💬 **Обратная связь и поддержка**

Твоё мнение важно для нас! Расскажи нам о своём опыте обучения в МосПолитехе.

**Варианты обратной связи:**
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить отзыв")],
            [KeyboardButton(text="🐛 Сообщить об ошибке")],
            [KeyboardButton(text="💡 Предложить новую функцию в боте")],
            [KeyboardButton(text="📞 Основные контакты поддержки")],
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(feedback_text, reply_markup=keyboard)


@router.message(F.text == "📝 Оставить отзыв")
async def handle_leave_review(message: types.Message):
    """Оставить отзыв"""
    review_text = """
📝 **Оставить отзыв о боте или сервисе:**

Спасибо за обратную связь! Отправь нам свой отзыв тремя способами:

📧 **Email:**
   feedback@mospolytech.ru
   Тема: "Отзыв о боте МосПолитеха"

📱 **Telegram:**
   @mospolytech_feedback
   Напиши своё сообщение

🌐 **Форма на сайте:**
   https://mospolytech.ru/feedback

📋 **Что включить в отзыв:**
   ✅ Что тебе нравится
   ✅ Что можно улучшить
   ✅ Какие функции ты хотел бы видеть
   ✅ Твой контакт (необязательно)

Все отзывы анонимны (если не указываешь контакт).
Результаты твоей обратной связи помогают нам совершенствоваться! 💪
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Обратная связь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(review_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "🐛 Сообщить об ошибке")
async def handle_report_bug(message: types.Message):
    """Сообщить об ошибке"""
    bug_text = """
🐛 **Сообщить об ошибке в боте:**

Нашёл ошибку? Помоги нам её исправить!

📧 **Отправь баг-рипорт на:**
   bugs@mospolytech.ru

📝 **В сообщении указа́й:**
   1️⃣ Что ты делал когда произошла ошибка
   2️⃣ Какой текст ошибки ты видел (если есть)
   3️⃣ На каком устройстве это произошло
   4️⃣ Твой номер группы (для контекста)

💡 **Примеры хороших баг-репортов:**
   ✅ "При нажатии на кнопку 'Расписание' бот молчит (30 сек) и ничего не происходит"
   ✅ "При вводе номера группы 'INVALID' бот выдал ошибку: 'TypeError'"
   ✅ "Кнопка 'Назад' не работает в подменю Студента"

📱 **Также можешь:** 
   Написать в Telegram: @mospolytech_tech_support

Спасибо за помощь в улучшении! 🙌
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Обратная связь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(bug_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "💡 Предложить новую функцию в боте")
async def handle_feature_request(message: types.Message):
    """Предложить новую функцию"""
    feature_text = """
💡 **Предложить новую функцию для бота:**

Есть идея, которая улучшит бот? Расскажи нам!

📧 **Отправь предложение на:**
   features@mospolytech.ru

📋 **Структура хорошего предложения:**
   1️⃣ Название функции
   2️⃣ Описание - что она будет делать
   3️⃣ Кому это нужно (студентам, абитуриентам, сотрудникам)
   4️⃣ Как это упростит жизнь (примеры)
   5️⃣ Примеры использования

💭 **Примеры успешных идей:**
   ✅ Уведомления о переносе пар
   ✅ Поиск по названию преподавателя
   ✅ Интеграция с 2ГИС для навигации в университет
   ✅ Напоминания о важных датах и сроках
   ✅ Рейтинг преподавателей от студентов

📱 **Также можешь:**
   1️⃣ Написать в Telegram: @mospolytech_ideas
   2️⃣ Использовать форму на сайте
   3️⃣ Рассказать разработчикам на ярмарке вакансий

Твои идеи помогают нам развиваться! 🚀
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Обратная связь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(feature_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "📞 Основные контакты поддержки")
async def handle_main_contacts(message: types.Message):
    """Основные контакты поддержки"""
    contacts_text = """
📞 **Основные контакты поддержки МосПолитеха:**

📱 **Главный номер университета:**
   +7 (495) 223-55-00
   Пн-Пт: 09:00-18:00

📧 **Email поддержки:**
   support@mospolytech.ru
   Ответ в течение 1-2 дней

📍 **Лично посетить:**
   Корпус 1, каб. 102 (информационный центр)
   Ул. Большая Семеновская, д. 38
   Москва, 107023

🚇 **Транспорт:**
   Метро "Красные Ворота" - 5 минут пешком
   Метро "Комсомольская" - 10 минут пешком

💬 **Социальные сети:**
   📱 Telegram: @mospolytech_support
   📱 VK: https://vk.com/mospolytech
   📱 Instagram: @mospolytech_official

🕐 **Горячая линия:**
   +7 (499) 000-00-00 (24/7 для срочных вопросов)

🌐 **Веб-форма обратной связи:**
   https://mospolytech.ru/support

Мы всегда готовы помочь! 😊
"""
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Обратная связь")],
            [KeyboardButton(text="🏠 Главное меню")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(contacts_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(F.text == "◀️ Назад")
async def handle_back(message: types.Message, state: FSMContext = None):
    """Обработчик для возврата в главное меню"""
    await message.answer("↩️ Возврат в главное меню", reply_markup=get_main_menu_keyboard())


@router.message()
async def default_handler(message: types.Message):
    """Обработчик для неизвестных сообщений"""
    default_text = (
        "Не понимаю твою команду 🤔\n\n"
        "Используй кнопки меню или команды:\n"
        "/start - начать\n"
        "/menu - главное меню\n"
        "/help - справка"
    )
    await message.answer(default_text, reply_markup=get_main_menu_keyboard())
