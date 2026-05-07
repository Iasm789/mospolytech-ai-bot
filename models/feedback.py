"""
Модель данных для системы обратной связи
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from datetime import datetime


@dataclass
class Feedback:
    """Модель отзыва/обратной связи"""
    
    feedback_id: str  # Уникальный идентификатор
    user_id: int  # Telegram user ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    
    # Тип обратной связи
    feedback_type: Literal["review", "bug_report", "feature_request", "improvement", "other"] = "review"
    
    # Содержание
    title: Optional[str] = None  # Заголовок (для bug_report и feature_request)
    message: str = ""  # Основное сообщение
    
    # Оценка проекта (1-5 звёзд, опционально)
    rating: Optional[int] = None
    
    # Служебные поля
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_resolved: bool = False
    admin_response: Optional[str] = None
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return asdict(self)
    
    def __repr__(self):
        return f"<Feedback(id={self.feedback_id}, user_id={self.user_id}, type={self.feedback_type})>"


@dataclass
class FeedbackStats:
    """Статистика обратной связи"""
    total_count: int = 0
    average_rating: float = 0.0
    by_type: dict = field(default_factory=dict)
    
    def __repr__(self):
        return f"<FeedbackStats(total={self.total_count}, avg_rating={self.average_rating})>"
