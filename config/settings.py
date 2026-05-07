"""
Конфигурация приложения.
Загружается из переменных окружения с валидацией.
"""

from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Основная конфигурация приложения с валидацией"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Bot configuration
    BOT_TOKEN: str = Field(..., min_length=10)
    DEBUG: bool = False

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "bot.log"
    MAX_LOG_SIZE: int = 10485760  # 10 MB

    # Admin IDs (comma-separated)
    ADMIN_IDS: str = ""

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW: int = 60

    # Sessions
    SESSION_TIMEOUT: int = 3600  # 1 hour

    # Timeouts
    REQUEST_TIMEOUT: int = 30
    PARSER_TIMEOUT: int = 60

    # Cache configuration
    CACHE_ENABLED: bool = True
    CACHE_DIR: str = "data/cache"
    CACHE_EXPIRY: int = 86400  # 24 hours

    # Feature flags
    USE_SELENIUM: bool = True
    ENABLE_NOTIFICATIONS: bool = True

    # Local LLM (RAG generation)
    LOCAL_LLM_ENABLED: bool = True
    LOCAL_LLM_API_URL: str = "http://127.0.0.1:11434/api/generate"
    # Для меньшей задержки укажи здесь lighter/quantized модель, доступную в Ollama.
    LOCAL_LLM_MODEL: str = "qwen2.5:7b-instruct"
    # Каскад моделей (через запятую): первая primary, остальные fallback.
    # Пример: "qwen2.5:7b-instruct, qwen2.5:3b, llama3.1:8b"
    LOCAL_LLM_MODELS: str = ""
    # Роутинг моделей: отдельные каскады для простых и сложных вопросов.
    LOCAL_LLM_SIMPLE_MODELS: str = ""
    LOCAL_LLM_COMPLEX_MODELS: str = ""
    LOCAL_LLM_COMPLEX_MIN_TOKENS: int = 10
    # Адаптация под пиковую нагрузку: ускоряем генерацию без полного отключения LLM.
    LOCAL_LLM_ADAPTIVE_LOAD_ENABLED: bool = True
    LOCAL_LLM_HIGH_LOAD_WAITERS_THRESHOLD: int = 3
    LOCAL_LLM_HIGH_LOAD_INFLIGHT_THRESHOLD: int = 4
    LOCAL_LLM_HIGH_LOAD_MAX_TOKENS: int = 280
    LOCAL_LLM_HIGH_LOAD_CONTEXT_FACTOR: float = 0.7
    LOCAL_LLM_TIMEOUT: int = 20
    LOCAL_LLM_TEMPERATURE: float = 0.15
    LOCAL_LLM_MAX_TOKENS: int = 500
    LOCAL_LLM_MAX_CONCURRENCY: int = 4
    LOCAL_LLM_MIN_CONFIDENCE_SCORE: float = 0.5
    LOCAL_LLM_MIN_CONFIDENCE_SCORE_WITH_TOPIC: float = 0.35
    # При очень коротких фрагментах в RAG — всё равно вызвать LLM с «осторожным» промптом (иначе шаблон с буллетами бесполезен)
    LOCAL_LLM_TRY_ON_SPARSE_CONTEXT: bool = True
    LOCAL_LLM_SPARSE_MIN_SCORE: float = 0.14
    LOCAL_LLM_CIRCUIT_FAILURES: int = 5
    LOCAL_LLM_CIRCUIT_COOLDOWN_SEC: int = 60
    LOCAL_INTENT_MIN_CONFIDENCE: float = 0.28
    LOCAL_AI_TOP_K: int = 5
    # Сколько кандидатов максимум взять на retrieval-этапе (до сжатия контекста).
    LOCAL_AI_RETRIEVAL_TOP_K: int = 12
    # Максимальный размер контекста (символов), который отправляем в LLM.
    LOCAL_AI_LLM_MAX_CONTEXT_CHARS: int = 4000
    LOCAL_AI_MAX_FACT_LINE_CHARS: int = 420
    LOCAL_AI_CACHE_TTL_SEC: int = 900
    LOCAL_AI_CACHE_MAX_SIZE: int = 500
    # Кэш результатов retrieval (отдельно от финального ответа; короче TTL — чаще обновлять контекст)
    LOCAL_AI_RETRIEVAL_CACHE_TTL_SEC: int = 600
    LOCAL_AI_RETRIEVAL_CACHE_MAX_SIZE: int = 1000
    # Прогрев локальной LLM при старте (снижает cold start первого запроса)
    LOCAL_LLM_WARMUP_ENABLED: bool = False
    LOCAL_LLM_WARMUP_TIMEOUT: int = 12
    LOCAL_AI_METRICS_LOG_EVERY: int = 50
    LOCAL_AI_MIN_FAQ_COVERAGE: float = 0.05
    LOCAL_AI_MIN_FAQ_MARGIN: float = 0.05
    LOCAL_EMBEDDINGS_ENABLED: bool = False
    LOCAL_EMBEDDINGS_API_URL: str = "http://127.0.0.1:11434/api/embeddings"
    LOCAL_EMBEDDINGS_MODEL: str = "nomic-embed-text"
    LOCAL_EMBEDDINGS_WEIGHT: float = 0.35
    QUALITY_REVIEW_LOG_DIR: str = "data/quality_review"
    ANSWER_PRIORITY: str = "llm_first"  # llm_first | faq_first

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Валидировать уровень логирования"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value not in valid_levels:
            raise ValueError(f"LOG_LEVEL должен быть одним из: {valid_levels}")
        return value

    @field_validator("ANSWER_PRIORITY")
    @classmethod
    def validate_answer_priority(cls, value: str) -> str:
        """Валидировать порядок источников ответа."""
        valid_priorities = ["llm_first", "faq_first"]
        if value not in valid_priorities:
            raise ValueError(f"ANSWER_PRIORITY должен быть одним из: {valid_priorities}")
        return value

    @field_validator(
        "RATE_LIMIT_REQUESTS",
        "RATE_LIMIT_WINDOW",
        "SESSION_TIMEOUT",
        "REQUEST_TIMEOUT",
        "PARSER_TIMEOUT",
        "CACHE_EXPIRY",
        "MAX_LOG_SIZE",
        "LOCAL_LLM_TIMEOUT",
        "LOCAL_LLM_MAX_TOKENS",
        "LOCAL_LLM_MAX_CONCURRENCY",
        "LOCAL_LLM_CIRCUIT_FAILURES",
        "LOCAL_LLM_CIRCUIT_COOLDOWN_SEC",
        "LOCAL_AI_TOP_K",
        "LOCAL_AI_RETRIEVAL_TOP_K",
        "LOCAL_AI_LLM_MAX_CONTEXT_CHARS",
        "LOCAL_AI_MAX_FACT_LINE_CHARS",
        "LOCAL_AI_CACHE_TTL_SEC",
        "LOCAL_AI_CACHE_MAX_SIZE",
        "LOCAL_AI_RETRIEVAL_CACHE_TTL_SEC",
        "LOCAL_AI_RETRIEVAL_CACHE_MAX_SIZE",
        "LOCAL_LLM_WARMUP_TIMEOUT",
        "LOCAL_AI_METRICS_LOG_EVERY",
        "LOCAL_LLM_COMPLEX_MIN_TOKENS",
        "LOCAL_LLM_HIGH_LOAD_WAITERS_THRESHOLD",
        "LOCAL_LLM_HIGH_LOAD_INFLIGHT_THRESHOLD",
        "LOCAL_LLM_HIGH_LOAD_MAX_TOKENS",
    )
    @classmethod
    def validate_positive_integers(cls, value: int) -> int:
        """Валидировать положительные целые числа"""
        if value <= 0:
            raise ValueError("Значение должно быть положительным числом")
        return value

    @field_validator("LOCAL_LLM_TEMPERATURE")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        """Валидировать температуру генерации LLM."""
        if not 0 <= value <= 1:
            raise ValueError("LOCAL_LLM_TEMPERATURE должно быть в диапазоне [0, 1]")
        return value

    @field_validator(
        "LOCAL_LLM_MIN_CONFIDENCE_SCORE",
        "LOCAL_LLM_MIN_CONFIDENCE_SCORE_WITH_TOPIC",
        "LOCAL_LLM_SPARSE_MIN_SCORE",
        "LOCAL_INTENT_MIN_CONFIDENCE",
        "LOCAL_AI_MIN_FAQ_COVERAGE",
        "LOCAL_AI_MIN_FAQ_MARGIN",
        "LOCAL_EMBEDDINGS_WEIGHT",
        "LOCAL_LLM_HIGH_LOAD_CONTEXT_FACTOR",
    )
    @classmethod
    def validate_confidence_threshold(cls, value: float) -> float:
        """Валидировать пороги confidence-gate для LLM."""
        if not 0 <= value <= 1:
            raise ValueError("Порог confidence должен быть в диапазоне [0, 1]")
        return value

    @field_validator("BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, value: str) -> str:
        """Валидировать токен бота"""
        if not value or len(value) < 20:
            raise ValueError("Неверный формат BOT_TOKEN")
        return value

    @property
    def admin_ids_list(self) -> list[int]:
        """Парсинг списка admin IDs с валидацией"""
        if not self.ADMIN_IDS:
            return []

        try:
            admin_ids = []
            for id_str in self.ADMIN_IDS.split(","):
                id_str = id_str.strip()
                if id_str and id_str.isdigit():
                    admin_ids.append(int(id_str))
            return admin_ids
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Ошибка при парсинге ADMIN_IDS: {e}")

    @property
    def local_llm_models_list(self) -> list[str]:
        """Список моделей в порядке приоритета (primary -> fallback)."""
        models: list[str] = []
        if self.LOCAL_LLM_MODELS:
            for model in self.LOCAL_LLM_MODELS.split(","):
                model = model.strip()
                if model:
                    models.append(model)
        if not models and self.LOCAL_LLM_MODEL:
            models.append(self.LOCAL_LLM_MODEL.strip())
        return models

    @property
    def local_llm_simple_models_list(self) -> list[str]:
        """Каскад моделей для простых вопросов."""
        models: list[str] = []
        if self.LOCAL_LLM_SIMPLE_MODELS:
            for model in self.LOCAL_LLM_SIMPLE_MODELS.split(","):
                model = model.strip()
                if model:
                    models.append(model)
        return models

    @property
    def local_llm_complex_models_list(self) -> list[str]:
        """Каскад моделей для сложных вопросов."""
        models: list[str] = []
        if self.LOCAL_LLM_COMPLEX_MODELS:
            for model in self.LOCAL_LLM_COMPLEX_MODELS.split(","):
                model = model.strip()
                if model:
                    models.append(model)
        return models


def validate_settings() -> Optional[str]:
    """
    Валидировать все параметры конфигурации

    Returns:
        Сообщение об ошибке или None если всё ОК
    """
    try:
        global settings
        settings = Settings()

        # Проверяем критические параметры
        if not settings.BOT_TOKEN:
            return "❌ Ошибка: BOT_TOKEN не установлен"

        # Логируем успешную инициализацию конфигурации
        from utils.logger import logger

        logger.info("✅ Конфигурация успешно загружена и валидирована")

        return None
    except ValidationError as e:
        error_msg = f"❌ Ошибка валидации конфигурации: {e}"
        return error_msg
    except Exception as e:
        error_msg = f"❌ Критическая ошибка конфигурации: {e}"
        return error_msg


# Инициализация конфигурации
try:
    settings = Settings()
except ValidationError as e:
    print(f"❌ Ошибка при загрузке конфигурации: {e}")
    raise
