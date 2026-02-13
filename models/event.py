from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Event:
    """Модель для мероприятий и ДОД"""
    title: str
    event_date: datetime
    event_type: str  # 'dod', 'seminar', 'meropriyatie'
    description: Optional[str] = None
    registration_url: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self):
        return f"<Event(title={self.title}, date={self.event_date})>"

