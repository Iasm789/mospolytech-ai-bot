"""
Модуль валидации входных данных
Обеспечивает безопасность и корректность обработки пользовательского ввода
"""

import re
from typing import Optional, Tuple

from config.constants import (
    MIN_GROUP_NUMBER_LENGTH, MAX_GROUP_NUMBER_LENGTH,
    GROUP_NUMBER_REGEX, MIN_SEARCH_LENGTH, MAX_SEARCH_QUERY_LENGTH
)
from utils.logger import logger


class ValidationError(Exception):
    """Ошибка валидации"""
    pass


class InputValidator:
    """Валидатор пользовательского ввода"""
    
    @staticmethod
    def validate_group_number(group_number: str) -> Tuple[bool, Optional[str]]:
        """
        Валидировать номер группы
        
        Args:
            group_number: Номер группы для проверки
        
        Returns:
            Tuple (валиден ли, сообщение об ошибке если есть)
        """
        if not group_number:
            return False, "❌ Номер группы не может быть пустым"
        
        # Очищаем от пробелов и конвертируем в верхний регистр
        group_number = group_number.strip().upper()
        
        # Проверяем длину
        if len(group_number) < MIN_GROUP_NUMBER_LENGTH:
            return False, f"❌ Номер группы слишком короткий (минимум {MIN_GROUP_NUMBER_LENGTH} символов)"
        
        if len(group_number) > MAX_GROUP_NUMBER_LENGTH:
            return False, f"❌ Номер группы слишком длинный (максимум {MAX_GROUP_NUMBER_LENGTH} символов)"
        
        # Проверяем формат (должен быть вида XXX-YYYY)
        if not re.match(GROUP_NUMBER_REGEX, group_number):
            return False, (
                "❌ Неверный формат номера группы.\n"
                "Используй формат: XXX-YYYY (например: 231-3310)"
            )
        
        return True, None
    
    @staticmethod
    def sanitize_group_number(group_number: str) -> str:
        """
        Очистить и нормализовать номер группы
        
        Args:
            group_number: Номер группы
        
        Returns:
            Очищенный номер группы
        """
        return group_number.strip().upper()
    
    @staticmethod
    def validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Валидировать поисковый запрос
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Tuple (валиден ли, сообщение об ошибке если есть)
        """
        if not query:
            return False, "❌ Поисковый запрос не может быть пустым"
        
        query = query.strip()
        
        if len(query) < MIN_SEARCH_LENGTH:
            return False, f"❌ Поисковый запрос слишком короткий (минимум {MIN_SEARCH_LENGTH} символов)"
        
        if len(query) > MAX_SEARCH_QUERY_LENGTH:
            return False, f"❌ Поисковый запрос слишком длинный (максимум {MAX_SEARCH_QUERY_LENGTH} символов)"
        
        return True, None
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """
        Очистить поисковый запрос от опасных символов
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Очищенный запрос
        """
        # Удаляем лишние пробелы
        query = query.strip()
        query = re.sub(r'\s+', ' ', query)
        
        # Удаляем потенциально опасные символы, но оставляем буквы, цифры и пропуски
        safe_query = re.sub(r'[^\w\s\-а-яА-ЯЁё]', '', query)
        
        return safe_query
    
    @staticmethod
    def validate_user_input(text: str, max_length: int = 1000) -> Tuple[bool, Optional[str]]:
        """
        Базовая валидация пользовательского ввода
        
        Args:
            text: Текст для валидации
            max_length: Максимальная длина текста
        
        Returns:
            Tuple (валиден ли, сообщение об ошибке если есть)
        """
        if not text:
            return False, "❌ Ввод не может быть пустым"
        
        if len(text) > max_length:
            return False, f"❌ Ввод слишком длинный (максимум {max_length} символов)"
        
        return True, None
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """
        Очистить текст от потенциально опасных элементов
        
        Args:
            text: Текст для очистки
            max_length: Максимальная длина текста
        
        Returns:
            Очищенный текст
        """
        # Удаляем лишние пробелы
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Ограничиваем длину
        if len(text) > max_length:
            text = text[:max_length].rstrip() + "..."
        
        return text


def validate_group_or_error(group_number: str) -> Optional[str]:
    """
    Валидировать номер группы и вернуть ошибку
    
    Args:
        group_number: Номер группы
    
    Returns:
        Сообщение об ошибке или None если валиден
    """
    is_valid, error_message = InputValidator.validate_group_number(group_number)
    if not is_valid:
        logger.warning(f"Невалиден номер группы: {group_number}")
        return error_message
    return None


def validate_search_or_error(query: str) -> Optional[str]:
    """
    Валидировать поисковый запрос и вернуть ошибку
    
    Args:
        query: Поисковый запрос
    
    Returns:
        Сообщение об ошибке или None если валиден
    """
    is_valid, error_message = InputValidator.validate_search_query(query)
    if not is_valid:
        logger.warning(f"Невалиден поисковый запрос: {query}")
        return error_message
    return None
