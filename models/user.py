from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Модель пользователя"""
    user_id: int  # Telegram user ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    group: Optional[str] = None  # Номер группы студента
    role: str = 'user'  # 'user', 'student', 'applicant', 'admin'
    
    # Подписки
    schedule_reminder: bool = False
    reminder_minutes: int = 30
    events_subscription: bool = False
    
    # Служебные поля
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"

