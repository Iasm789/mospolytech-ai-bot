from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class FAQ:
    """Модель часто задаваемых вопросов"""
    question: str
    answer: str
    category: str  # 'applicant', 'student', 'general'
    tags: Optional[str] = None  # Разделённые запятыми теги для поиска
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self):
        return f"<FAQ(category={self.category}, question={self.question[:50]})>"

