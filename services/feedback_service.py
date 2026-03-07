"""
Сервис управления обратной связью
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Literal
from pathlib import Path
import uuid

from models.feedback import Feedback, FeedbackStats
from utils.logger import logger


FEEDBACK_FILE = Path(__file__).parent.parent / "docs" / "feedback.json"


class FeedbackService:
    """Сервис для управления отзывами и обратной связью"""
    
    def __init__(self, file_path: Path = FEEDBACK_FILE):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Убедиться, что файл обратной связи существует"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.file_path.exists():
            self._save_data([])
            logger.info(f"✅ Создан файл обратной связи: {self.file_path}")
    
    def _load_data(self) -> List[dict]:
        """Загрузить все отзывы из JSON"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке обратной связи: {e}")
            return []
    
    def _save_data(self, data: List[dict]):
        """Сохранить отзывы в JSON"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Обратная связь сохранена")
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении обратной связи: {e}")
    
    def add_feedback(self, feedback: Feedback) -> bool:
        """Добавить новый отзыв"""
        try:
            # Генерируем уникальный ID если не задан
            if not feedback.feedback_id:
                feedback.feedback_id = str(uuid.uuid4())
            
            data = self._load_data()
            data.append(feedback.to_dict())
            self._save_data(data)
            
            logger.info(f"✅ Отзыв добавлен: {feedback.feedback_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении отзыва: {e}")
            return False
    
    def get_all_feedback(self) -> List[Feedback]:
        """Получить все отзывы"""
        try:
            data = self._load_data()
            feedback_list = []
            for item in data:
                feedback = Feedback(**item)
                feedback_list.append(feedback)
            return feedback_list
        except Exception as e:
            logger.error(f"❌ Ошибка при получении отзывов: {e}")
            return []
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[Feedback]:
        """Получить отзыв по ID"""
        try:
            data = self._load_data()
            for item in data:
                if item['feedback_id'] == feedback_id:
                    return Feedback(**item)
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении отзыва: {e}")
            return None
    
    def get_feedback_by_user(self, user_id: int) -> List[Feedback]:
        """Получить все отзывы пользователя"""
        try:
            data = self._load_data()
            feedback_list = []
            for item in data:
                if item['user_id'] == user_id:
                    feedback = Feedback(**item)
                    feedback_list.append(feedback)
            return feedback_list
        except Exception as e:
            logger.error(f"❌ Ошибка при получении отзывов пользователя: {e}")
            return []
    
    def get_feedback_by_type(self, feedback_type: str) -> List[Feedback]:
        """Получить отзывы определённого типа"""
        try:
            data = self._load_data()
            feedback_list = []
            for item in data:
                if item['feedback_type'] == feedback_type:
                    feedback = Feedback(**item)
                    feedback_list.append(feedback)
            return feedback_list
        except Exception as e:
            logger.error(f"❌ Ошибка при фильтрации отзывов: {e}")
            return []
    
    def get_stats(self) -> FeedbackStats:
        """Получить статистику по отзывам"""
        try:
            all_feedback = self.get_all_feedback()
            
            if not all_feedback:
                return FeedbackStats()
            
            # Подсчитываем статистику
            total = len(all_feedback)
            
            # Количество по типам
            by_type = {}
            ratings = []
            
            for fb in all_feedback:
                # Считаем по типам
                fb_type = fb.feedback_type
                by_type[fb_type] = by_type.get(fb_type, 0) + 1
                
                # Собираем оценки
                if fb.rating is not None:
                    ratings.append(fb.rating)
            
            # Вычисляем среднюю оценку
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            return FeedbackStats(
                total_count=total,
                average_rating=round(avg_rating, 2),
                by_type=by_type
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при подсчёте статистики: {e}")
            return FeedbackStats()
    
    def update_feedback(self, feedback_id: str, **kwargs) -> bool:
        """Обновить отзыв"""
        try:
            data = self._load_data()
            for item in data:
                if item['feedback_id'] == feedback_id:
                    item.update(kwargs)
                    self._save_data(data)
                    logger.info(f"✅ Отзыв обновлён: {feedback_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении отзыва: {e}")
            return False
    
    def delete_feedback(self, feedback_id: str) -> bool:
        """Удалить отзыв"""
        try:
            data = self._load_data()
            new_data = [item for item in data if item['feedback_id'] != feedback_id]
            
            if len(new_data) < len(data):
                self._save_data(new_data)
                logger.info(f"✅ Отзыв удалён: {feedback_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении отзыва: {e}")
            return False
    
    def get_unresolved_feedback(self) -> List[Feedback]:
        """Получить нерешённые отзывы (для администраторов)"""
        try:
            data = self._load_data()
            feedback_list = []
            for item in data:
                if not item['is_resolved']:
                    feedback = Feedback(**item)
                    feedback_list.append(feedback)
            return feedback_list
        except Exception as e:
            logger.error(f"❌ Ошибка при получении нерешённых отзывов: {e}")
            return []
    
    def get_recent_feedback(self, limit: int = 10) -> List[Feedback]:
        """Получить последние N отзывов"""
        try:
            all_feedback = self.get_all_feedback()
            # Сортируем по дате (новые сначала)
            sorted_feedback = sorted(
                all_feedback,
                key=lambda x: x.created_at,
                reverse=True
            )
            return sorted_feedback[:limit]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении последних отзывов: {e}")
            return []


# Глобальный экземпляр сервиса
feedback_service: Optional[FeedbackService] = None


async def init_feedback_service() -> FeedbackService:
    """Инициализировать сервис обратной связи"""
    global feedback_service
    if feedback_service is None:
        feedback_service = FeedbackService()
        logger.info("✅ Сервис обратной связи инициализирован")
    return feedback_service


def get_feedback_service() -> FeedbackService:
    """Получить экземпляр сервиса обратной связи"""
    global feedback_service
    if feedback_service is None:
        feedback_service = FeedbackService()
    return feedback_service
