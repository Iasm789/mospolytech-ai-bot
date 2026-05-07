#!/usr/bin/env python3
"""
Скрипт для демонстрации и управления системой обратной связи

Использование:
    python scripts/manage_feedback.py --list          # Показать все отзывы
    python scripts/manage_feedback.py --stats         # Показать статистику
    python scripts/manage_feedback.py --user 123456   # Отзывы пользователя
    python scripts/manage_feedback.py --type review   # Отзывы определённого типа
    python scripts/manage_feedback.py --recent 5      # Последние N отзывов
    python scripts/manage_feedback.py --export csv    # Экспортировать в CSV
"""

import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Optional

# Добавить родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.feedback_service import get_feedback_service
from models.feedback import Feedback


def print_feedback(feedback: Feedback, show_all: bool = False):
    """Красиво вывести информацию об отзыве"""
    type_emoji = {
        "review": "⭐",
        "bug_report": "🐛",
        "improvement": "💡",
        "other": "📋"
    }
    
    emoji = type_emoji.get(feedback.feedback_type, "📝")
    
    print(f"\n{emoji} ID: {feedback.feedback_id}")
    print(f"👤 От: {feedback.first_name} (@{feedback.username})")
    
    if feedback.rating:
        print(f"⭐ Оценка: {'★' * feedback.rating}{'☆' * (5 - feedback.rating)}")
    
    if feedback.title:
        print(f"📌 Заголовок: {feedback.title}")
    
    if show_all or len(feedback.message) <= 100:
        print(f"📝 Сообщение: {feedback.message}")
    else:
        print(f"📝 Сообщение: {feedback.message[:100]}...")
    
    print(f"📅 Дата: {feedback.created_at}")
    
    if feedback.phone or feedback.email:
        contacts = []
        if feedback.phone:
            contacts.append(f"📱 {feedback.phone}")
        if feedback.email:
            contacts.append(f"📧 {feedback.email}")
        print(f"Контакты: {', '.join(contacts)}")
    
    if feedback.is_resolved:
        print(f"✅ Статус: РАЗРЕШЕНО")
        if feedback.admin_response:
            print(f"💬 Ответ: {feedback.admin_response}")
    else:
        print(f"⏳ Статус: В ОЖИДАНИИ")
    
    print("-" * 60)


def list_all_feedback():
    """Показать все отзывы"""
    service = get_feedback_service()
    all_feedback = service.get_all_feedback()
    
    if not all_feedback:
        print("❌ Нет отзывов")
        return
    
    print(f"\n📊 Всего отзывов: {len(all_feedback)}\n")
    
    for fb in all_feedback:
        print_feedback(fb)


def show_stats():
    """Показать статистику"""
    service = get_feedback_service()
    stats = service.get_stats()
    
    print(f"\n📊 СТАТИСТИКА ОБРАТНОЙ СВЯЗИ")
    print(f"=" * 60)
    print(f"Всего отзывов: {stats.total_count}")
    
    if stats.average_rating > 0:
        print(f"Средняя оценка: {'⭐' * int(stats.average_rating)} {stats.average_rating}/5.0")
    else:
        print(f"Средняя оценка: Нет оценок")
    
    print(f"\nПо типам:")
    type_names = {
        "review": "⭐ Отзывы",
        "bug_report": "🐛 Баг-репорты",
        "improvement": "💡 Предложения/улучшения",
        "other": "📋 Прочее"
    }
    
    for fb_type, count in sorted(stats.by_type.items()):
        type_name = type_names.get(fb_type, fb_type)
        print(f"  {type_name}: {count}")
    
    print("=" * 60)


def show_user_feedback(user_id: int):
    """Показать отзывы пользователя"""
    service = get_feedback_service()
    user_feedback = service.get_feedback_by_user(user_id)
    
    if not user_feedback:
        print(f"❌ Отзывов от пользователя {user_id} не найдено")
        return
    
    print(f"\n👤 Отзывы пользователя {user_id} ({len(user_feedback)} шт.)\n")
    
    for fb in user_feedback:
        print_feedback(fb)


def show_type_feedback(feedback_type: str):
    """Показать отзывы определённого типа"""
    service = get_feedback_service()
    type_feedback = service.get_feedback_by_type(feedback_type)
    
    if not type_feedback:
        print(f"❌ Отзывов типа '{feedback_type}' не найдено")
        return
    
    type_names = {
        "review": "⭐ Отзывы",
        "bug_report": "🐛 Баг-репорты",
        "improvement": "💡 Предложения/улучшения",
        "other": "📋 Прочее"
    }
    
    type_name = type_names.get(feedback_type, feedback_type)
    print(f"\n{type_name} ({len(type_feedback)} шт.)\n")
    
    for fb in type_feedback:
        print_feedback(fb)


def show_recent_feedback(limit: int = 10):
    """Показать последние отзывы"""
    service = get_feedback_service()
    recent = service.get_recent_feedback(limit)
    
    if not recent:
        print("❌ Нет отзывов")
        return
    
    print(f"\n📅 Последние {limit} отзывов\n")
    
    for fb in recent:
        print_feedback(fb)


def export_to_csv(output_file: Optional[str] = None):
    """Экспортировать отзывы в CSV"""
    service = get_feedback_service()
    all_feedback = service.get_all_feedback()
    
    if not all_feedback:
        print("❌ Нет отзывов для экспорта")
        return
    
    output_path = output_file or "feedback_export.csv"
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'feedback_id', 'user_id', 'username', 'first_name',
                'phone', 'email', 'feedback_type', 'title', 'message',
                'rating', 'created_at', 'is_resolved', 'admin_response'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for fb in all_feedback:
                writer.writerow({
                    'feedback_id': fb.feedback_id,
                    'user_id': fb.user_id,
                    'username': fb.username,
                    'first_name': fb.first_name,
                    'phone': fb.phone,
                    'email': fb.email,
                    'feedback_type': fb.feedback_type,
                    'title': fb.title,
                    'message': fb.message,
                    'rating': fb.rating,
                    'created_at': fb.created_at,
                    'is_resolved': fb.is_resolved,
                    'admin_response': fb.admin_response,
                })
        
        print(f"✅ Экспортировано {len(all_feedback)} отзывов в {output_path}")
    
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")


def export_to_json(output_file: Optional[str] = None):
    """Экспортировать отзывы в JSON"""
    service = get_feedback_service()
    all_feedback = service.get_all_feedback()
    
    if not all_feedback:
        print("❌ Нет отзывов для экспорта")
        return
    
    output_path = output_file or "feedback_export.json"
    
    try:
        data = [fb.to_dict() for fb in all_feedback]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Экспортировано {len(all_feedback)} отзывов в {output_path}")
    
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")


def mark_resolved(feedback_id: str, response: str = ""):
    """Отметить отзыв как разрешённый"""
    service = get_feedback_service()
    
    kwargs = {"is_resolved": True}
    if response:
        kwargs["admin_response"] = response
    
    if service.update_feedback(feedback_id, **kwargs):
        print(f"✅ Отзыв {feedback_id} отмечен как разрешённый")
    else:
        print(f"❌ Отзыв {feedback_id} не найден")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Управление системой обратной связи"
    )
    
    parser.add_argument(
        '--list', action='store_true',
        help='Показать все отзывы'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='Показать статистику'
    )
    parser.add_argument(
        '--user', type=int,
        help='Показать отзывы пользователя (user_id)'
    )
    parser.add_argument(
        '--type', type=str,
        help='Показать отзывы типа (review, bug_report, improvement, other)'
    )
    parser.add_argument(
        '--recent', type=int, nargs='?', const=10,
        help='Показать последние N отзывов (по умолчанию 10)'
    )
    parser.add_argument(
        '--export', type=str, nargs='?', const='csv',
        help='Экспортировать (csv или json)'
    )
    parser.add_argument(
        '--output', type=str,
        help='Файл для экспорта'
    )
    parser.add_argument(
        '--resolve', type=str,
        help='Отметить отзыв как разрешённый (feedback_id)'
    )
    parser.add_argument(
        '--response', type=str,
        help='Добавить ответ при разрешении'
    )
    
    args = parser.parse_args()
    
    # Если нет аргументов - показать помощь
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    if args.list:
        list_all_feedback()
    
    elif args.stats:
        show_stats()
    
    elif args.user:
        show_user_feedback(args.user)
    
    elif args.type:
        show_type_feedback(args.type)
    
    elif args.recent is not None:
        show_recent_feedback(args.recent)
    
    elif args.export:
        output_file = args.output
        if args.export.lower() == 'csv':
            export_to_csv(output_file)
        elif args.export.lower() == 'json':
            export_to_json(output_file)
        else:
            print("❌ Неизвестный формат. Используйте 'csv' или 'json'")
    
    elif args.resolve:
        response = args.response or ""
        mark_resolved(args.resolve, response)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
