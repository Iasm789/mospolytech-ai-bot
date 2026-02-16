"""
Обработчики для работы с расписанием
"""

from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import re

from services.schedule_parser import parser
from utils.logger import logger

router = Router()


class ScheduleForm(StatesGroup):
    """Состояния для запроса расписания"""
    waiting_for_group = State()
    waiting_for_period = State()


# Иконки для типов занятий
LESSON_ICONS = {
    "Лекция": "🎓",
    "Практика": "💻",
    "Лабораторная": "🔬",
    "Семинар": "📝",
    "Экзамен": "📝",
    "Зачёт": "✅",
}


def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨‍🎓 Абитуриенту"), KeyboardButton(text="📚 Студенту")],
            [KeyboardButton(text="📰 Новости"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="💬 Обратная связь")],
        ],
        resize_keyboard=True
    )


@router.message(F.text == "📅 Расписание занятий")
async def ask_for_group(message: types.Message, state: FSMContext):
    """Запрос номера группы"""
    await state.set_state(ScheduleForm.waiting_for_group)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Отмена")],
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📝 Введи номер группы (например, <code>231-3310</code>):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(ScheduleForm.waiting_for_group)
async def get_group_ask_period(message: types.Message, state: FSMContext):
    """Получить группу и запросить период"""
    group = message.text.strip().upper()
    
    # Проверяем если это отмена
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена", reply_markup=get_main_menu_keyboard())
        return
    
    # Проверяем формат группы
    if not group or len(group) < 4:
        await message.answer("❌ Неверный формат группы. Используй формат: XXX-YYYY")
        return
    
    # Проверяем наличие группы в списке
    if not parser.is_group_valid(group):
        await message.answer(
            f"❌ Группа <b>{group}</b> не найдена в списке доступных.\n\n"
            "Возможные причины:\n"
            "• Ошибка в номере группы\n"
            "• Расписание для этой группы недоступно\n\n"
            "Проверь номер и попробуй снова.",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем группу в контексте
    await state.update_data(group=group)
    
    # Переходим на выбор периода
    await state.set_state(ScheduleForm.waiting_for_period)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 На сегодня")],
            [KeyboardButton(text="📆 На неделю")],
            [KeyboardButton(text="◀️ Отмена")],
        ],
        resize_keyboard=True
    )
    
    today = datetime.now()
    today_date = today.strftime("%d.%m.%Y")
    days_ru = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    today_day = days_ru[today.weekday()]
    
    await message.answer(
        f"📅 Выбери период для группы <b>{group}</b>\n\n"
        f"Сегодня: {today_date} ({today_day})",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


def format_schedule_for_period(schedule: dict, group: str, period: str) -> str:
    """
    Форматировать расписание для выбранного периода
    
    Args:
        schedule: Полное расписание
        group: Номер группы
        period: "today" или "week"
    
    Returns:
        Форматированное расписание
    """
    if not schedule:
        return f"❌ Не удалось получить расписание для группы {group}"
    
    days = schedule.get('days', {})
    if not days:
        return f"❌ В расписании нет занятий для группы {group}"
    
    # Определяем дату и дни для отображения
    today = datetime.now()
    today_weekday = today.isoweekday()  # 1 = пн, 7 = вс
    
    # Маппинг номеров дней недели на ключи в расписании
    weekday_mapping = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
        7: "Воскресенье",
    }
    
    response = []
    
    # Определяем какие дни показывать
    if period == "today":
        # Показываем только сегодняшний день
        today_key = weekday_mapping.get(today_weekday)
        if today_key in days:
            days_to_show = {today_key: days[today_key]}
            period_text = f"📅 На сегодня ({today.strftime('%d.%m.%Y')})"
        else:
            return f"❌ На сегодня ({today.strftime('%d.%m.%Y')}) занятий нет"
    else:  # week
        # Показываем расписание на 7 дней
        days_to_show = {}
        # Берём расписание на 7 дней с сегодня
        for i in range(7):
            check_date = today + timedelta(days=i)
            check_weekday = check_date.isoweekday()
            day_key = weekday_mapping.get(check_weekday)
            if day_key and day_key in days and day_key not in days_to_show:
                days_to_show[day_key] = days[day_key]
        
        end_date = today + timedelta(days=6)
        period_text = f"📅 На неделю ({today.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')})"
    
    response.append(f"\n<b>{period_text}</b>")
    response.append("─" * 32)
    
    if not days_to_show:
        response.append("✨ В выбранный период занятий нет")
        return "\n".join(response)
    
    # Выводим каждый день отдельно
    for day_label, day_info in sorted(days_to_show.items()):
        response.append(f"\n<b>📅 {day_label}</b>")
        response.append("─" * 32)
        
        lessons = day_info.get('lessons', [])
        
        if not lessons:
            response.append("✨ Выходной день")
            continue
        
        # Фильтруем уроки по дате (только актуальные)
        filtered_lessons = parser.filter_lessons_by_date(lessons, today)
        
        if not filtered_lessons:
            response.append("✨ В этот день нет актуальных занятий")
            continue
        
        # Группируем уроки по времени дня (утро/день/вечер)
        periods = {
            'morning': {'icon': '🌅', 'name': 'УТРО', 'lessons': []},
            'afternoon': {'icon': '☀️', 'name': 'ДЕНЬ', 'lessons': []},
            'evening': {'icon': '🌙', 'name': 'ВЕЧЕР', 'lessons': []},
            'unknown': {'icon': '⏰', 'name': 'ДРУГОЕ', 'lessons': []}
        }
        
        # Сортируем уроки по времени
        sorted_lessons = sorted(filtered_lessons, key=lambda x: x.get('time_slot', 999))
        
        # Распределяем в периоды
        for lesson in sorted_lessons:
            period_key = lesson.get('time_period', 'unknown')
            periods[period_key]['lessons'].append(lesson)
        
        # Выводим каждый период отдельно
        for period_key in ['morning', 'afternoon', 'evening']:
            period_info = periods[period_key]
            
            if not period_info['lessons']:
                continue
            
            # Заголовок периода
            response.append(f"\n<b>{period_info['icon']} {period_info['name']}</b>")
            response.append("─" * 40)
            
            # Выводим уроки в этом периоде
            for lesson in period_info['lessons']:
                # Номер пары и время
                lesson_number = lesson.get('lesson_number', 'Пара ?')
                time_str = lesson.get('time_str', '??:?? - ??:??')
                
                # Тип занятия с иконкой
                lesson_type = lesson.get('type', 'Занятие')
                icon = LESSON_ICONS.get(lesson_type, "📚")
                
                # Название предмета
                subject = lesson.get('subject', 'N/A')
                
                response.append(f"\n<b>{lesson_number} пара | ⏰ {time_str}</b>")
                response.append(f"<b>{icon} {lesson_type}</b> — {subject}")
                
                # Преподаватель(и)
                teachers = lesson.get('teachers', [])
                if teachers:
                    teacher_names = [t.get('name', '') for t in teachers if isinstance(t, dict)]
                    if teacher_names:
                        response.append(f"👨‍🏫 {', '.join(teacher_names)}")
                elif lesson.get('teacher'):
                    response.append(f"👨‍🏫 {lesson['teacher']}")
                
                # Аудитория/Локация
                classrooms = lesson.get('classrooms', [])
                location = lesson.get('location', '')
                
                if classrooms:
                    response.append(f"🏫 Аудитория: {', '.join(classrooms)}")
                
                if location:
                    response.append(f"📍 {location}")
                
                # Период проведения
                period_info = lesson.get('period', '')
                if period_info:
                    response.append(f"📋 {period_info}")
                
                # Ссылка на онлайн занятие (если есть)
                webinar_url = lesson.get('webinar_url')
                if webinar_url:
                    response.append(f"🌐 <a href='{webinar_url}'>Онлайн занятие</a>")
    
    return "\n".join(response)


@router.message(ScheduleForm.waiting_for_period)
async def get_schedule(message: types.Message, state: FSMContext):
    """Получить и вывести расписание на выбранный период"""
    period_choice = message.text.strip()
    
    # Проверяем выбор периода
    if period_choice == "◀️ Отмена":
        await state.clear()
        await message.answer("❌ Отмена", reply_markup=get_main_menu_keyboard())
        return
    
    # Определяем период
    if period_choice == "📅 На сегодня":
        period = "today"
    elif period_choice == "📆 На неделю":
        period = "week"
    else:
        await message.answer("❌ Выбери либо 'На сегодня' либо 'На неделю'")
        return
    
    # Получаем сохранённую группу
    data = await state.get_data()
    group = data.get('group')
    
    if not group:
        await message.answer("❌ Группа не сохранена. Начни сначала.", reply_markup=get_main_menu_keyboard())
        await state.clear()
        return
    
    await message.answer("⏳ Загружаю расписание...")
    
    try:
        logger.info(f"Запрос расписания для группы: {group}, период: {period}")
        schedule = parser.get_schedule_by_group(group)
        
        if not schedule:
            await message.answer(
                f"❌ Не удалось получить расписание для группы <b>{group}</b>.\n\n"
                "Попробуй позже или проверь номер группы.",
                parse_mode="HTML"
            )
            return
        
        # Форматируем расписание для выбранного периода
        formatted_schedule = format_schedule_for_period(schedule, group, period)
        
        # Разбиваем на части если сообщение слишком длинное
        if len(formatted_schedule) > 4090:
            parts = []
            current_part = []
            current_length = 0
            
            for line in formatted_schedule.split('\n'):
                line_length = len(line) + 1  # +1 для переноса строки
                if current_length + line_length > 4000:
                    if current_part:
                        parts.append('\n'.join(current_part))
                    current_part = [line]
                    current_length = line_length
                else:
                    current_part.append(line)
                    current_length += line_length
            
            if current_part:
                parts.append('\n'.join(current_part))
            
            # Отправляем все части
            for i, part in enumerate(parts):
                if part.strip():
                    await message.answer(part, parse_mode="HTML")
                if i < len(parts) - 1:
                    await message.answer("─" * 50)
        else:
            await message.answer(formatted_schedule, parse_mode="HTML")
        
        logger.info(f"✅ Расписание отправлено для группы {group}")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при получении расписания: {e}")
        await message.answer(f"❌ Ошибка при загрузке расписания: {str(e)[:100]}")
    
    finally:
        await state.clear()
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Расписание")],
                [KeyboardButton(text="◀️ Назад")],
            ],
            resize_keyboard=True
        )
        await message.answer("Что дальше?", reply_markup=keyboard)
