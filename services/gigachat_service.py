"""
Сервис для интеграции с GigaChat API
"""

import requests
import base64
import uuid
import time
from typing import Optional, List, Dict
import logging

from config.settings import settings
from utils.logger import logger


class GigaChatService:
    """Сервис для работы с GigaChat API"""
    
    def __init__(self):
        """Инициализация сервиса GigaChat"""
        self.client_id = settings.GIGACHAT_CLIENT_ID
        self.client_secret = settings.GIGACHAT_CLIENT_SECRET
        self.scope = settings.GIGACHAT_SCOPE
        self.auth_url = settings.GIGACHAT_AUTH_URL
        self.api_url = settings.GIGACHAT_API_URL
        self.model = settings.GIGACHAT_MODEL
        
        self.access_token = None
        self.token_expires_at = 0
        
        # Проверяем что настроены credentials
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ GigaChat credentials не заполнены в .env файле!")
    
    def _get_auth_header(self) -> str:
        """Получить заголовок Authorization для получения токена"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _get_rq_uid(self) -> str:
        """Генерировать уникальный UUID для запроса"""
        return str(uuid.uuid4())
    
    def get_token(self) -> Optional[str]:
        """
        Получить токен доступа через OAuth 2.0
        
        Returns:
            Токен доступа или None если ошибка
        """
        try:
            # Проверяем что текущий токен ещё не истёк
            if self.access_token and time.time() < self.token_expires_at - 60:
                logger.debug(f"🔄 Используем кэшированный токен (истекает через {self.token_expires_at - time.time():.0f}сек)")
                return self.access_token
            
            logger.info("🔑 Получаю новый токен GigaChat...")
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': self._get_rq_uid(),
                'Authorization': self._get_auth_header()
            }
            
            data = {
                'scope': self.scope
            }
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                verify=False  # Отключаем проверку SSL (для локального тестирования)
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                # API возвращает expires_in (секунды), конвертируем в абсолютное время
                expires_in = result.get('expires_in', 1800)  # 30 минут по умолчанию
                self.token_expires_at = time.time() + expires_in
                
                logger.info(f"✅ Токен получен! Истекает через {expires_in} секунд")
                return self.access_token
            else:
                logger.error(f"❌ Ошибка получения токена: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Ошибка при получении токена: {e}")
            return None
    
    def chat(self, message: str, history: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Отправить сообщение в GigaChat
        
        Args:
            message: Текст сообщения
            history: История сообщений (опционально)
        
        Returns:
            Ответ GigaChat или None если ошибка
        """
        try:
            # Получаем токен
            token = self.get_token()
            if not token:
                logger.error("❌ Не удалось получить токен GigaChat")
                return None
            
            logger.info(f"💬 Отправляю сообщение: {message[:50]}...")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Строим историю сообщений
            messages = history or []
            
            # Добавляем новое сообщение
            messages.append({
                "role": "user",
                "content": message
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.1,
                "n": 1,
                "stream": False,
                "max_tokens": 512
            }
            
            url = f"{self.api_url}/chat/completions"
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                logger.info(f"✅ Ответ получен: {reply[:50]}...")
                return reply
            else:
                logger.error(f"❌ Ошибка при отправке сообщения: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Ошибка в методе chat: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Проверить настроены ли credentials GigaChat"""
        return bool(self.client_id and self.client_secret)


# Глобальный экземпляр сервиса
gigachat_service = GigaChatService()
