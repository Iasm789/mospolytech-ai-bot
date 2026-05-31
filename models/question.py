from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class AnonymousQuestion:
    """Модель для анонимных вопросов"""
    user_id: int  # ID пользователя (не раскрывается)
    question: str
    status: str = 'new'  # 'new', 'answered', 'closed'
    answer: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    answered_at: Optional[datetime] = None
    
    def __repr__(self):
        return f"<AnonymousQuestion(id={id(self)}, status={self.status})>"

