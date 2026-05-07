"""
Локальный AI fallback для ответов по JSON-данным проекта.

Без внешних API: сервис индексирует локальные JSON-файлы и формирует
ответ по наиболее релевантным фрагментам.
"""

from __future__ import annotations

import asyncio
import copy
import difflib
import json
import math
import re
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

import requests

from config.settings import settings
from utils.logger import logger


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Поддержка обеих структур, чтобы не ломаться из-за различий в названии папок.
DEFAULT_DATA_DIRS = (
    PROJECT_ROOT / "docs",
    PROJECT_ROOT / "docs" / "json",
    PROJECT_ROOT / "docss",
    PROJECT_ROOT / "docss" / "json",
)


@dataclass
class KnowledgeChunk:
    """Нормализованный фрагмент знания из JSON."""

    source: str
    path: str
    text: str
    embedding: list[float] | None = None


@dataclass(frozen=True)
class TopicRule:
    """Правила тематического роутинга."""

    name: str
    keywords: tuple[str, ...]
    source_hints: tuple[str, ...]


@dataclass
class RetrievalResult:
    """Результат retrieval-этапа RAG."""

    topic_name: str | None
    fact_lines: list[str]
    used_sources: list[str]
    top_score: float
    coverage_score: float


@dataclass
class CacheEntry:
    """Элемент кэша ответов."""

    answer_text: str
    expires_at: float


@dataclass
class RetrievalCacheEntry:
    """Элемент кэша этапа retrieval (до генерации LLM)."""

    retrieval: RetrievalResult
    expires_at: float


def normalize_text(text: str) -> str:
    """Нормализация текста для поиска."""
    lowered = text.lower().strip().replace("ё", "е")
    return re.sub(r"\s+", " ", lowered)


def normalize_question_key(text: str) -> str:
    """
    Ключ для кэша и дедупликации: базовая нормализация + снятие пунктуации,
    чтобы «вопрос?» и «вопрос» совпадали.
    """
    base = normalize_text(text)
    base = re.sub(r"[^\s\u0400-\u04FFa-z0-9]+", " ", base, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", base).strip()


def tokenize(text: str) -> set[str]:
    """Токенизация на слова/числа."""
    normalized = normalize_text(text)
    return set(re.findall(r"[a-zа-я0-9]+", normalized))


class LocalAIService:
    """Локальный сервис ответа на вопросы по JSON-источникам."""

    TOPIC_RULES: tuple[TopicRule, ...] = (
        TopicRule(
            name="scholarships",
            keywords=("стипенд", "выплат", "академ", "социал", "матпомощ"),
            source_hints=("scholar", "stipend"),
        ),
        TopicRule(
            name="dormitories",
            keywords=("общежит", "общаг", "заселен", "комнат", "проживан"),
            source_hints=("dorm", "hostel"),
        ),
        TopicRule(
            name="mfc",
            keywords=("мфц", "справк", "услуг", "документ", "заявлен"),
            source_hints=("mfc",),
        ),
        TopicRule(
            name="schedule",
            keywords=("расписан", "пары", "заняти", "урок", "групп"),
            source_hints=("schedule", "rasp"),
        ),
    )

    def __init__(self, data_dirs: tuple[Path, ...] | None = None):
        self.data_dirs = data_dirs or DEFAULT_DATA_DIRS
        self._chunks: list[KnowledgeChunk] = []
        # Ограничиваем число одновременных генераций, чтобы не перегружать локальную LLM.
        self._llm_semaphore = asyncio.Semaphore(settings.LOCAL_LLM_MAX_CONCURRENCY)
        self._inflight_lock = asyncio.Lock()
        self._inflight_answers: dict[str, asyncio.Future[str | None]] = {}
        self._answer_cache: dict[str, CacheEntry] = {}
        self._retrieval_cache: dict[str, RetrievalCacheEntry] = {}
        self._embedding_cache: dict[str, list[float]] = {}
        self._llm_circuit_failures = 0
        self._llm_circuit_open_until = 0.0
        self._llm_waiting_requests = 0
        self._llm_inflight_requests = 0
        self._llm_load_lock = asyncio.Lock()
        self._llm_last_mode = "normal"
        self._metrics = {
            "requests_total": 0,
            "cache_hits": 0,
            "retrieval_cache_hits": 0,
            "retrieval_misses": 0,
            "llm_success": 0,
            "llm_failures": 0,
            "template_fallbacks": 0,
            "inflight_dedup_hits": 0,
            "circuit_open_skips": 0,
            "high_load_activations": 0,
        }

    def build_index(self) -> int:
        """Построить индекс знаний из доступных JSON/TXT-файлов."""
        chunks: list[KnowledgeChunk] = []

        for data_dir in self.data_dirs:
            if not data_dir.exists() or not data_dir.is_dir():
                continue

            for json_file in data_dir.rglob("*.json"):
                # Не включаем пользовательскую обратную связь в LLM-fallback.
                if json_file.name == "feedback.json":
                    continue

                file_chunks = self._extract_chunks_from_file(json_file)
                chunks.extend(file_chunks)

            for text_file in data_dir.rglob("*.txt"):
                file_chunks = self._extract_chunks_from_txt_file(text_file)
                chunks.extend(file_chunks)

        self._chunks = chunks
        self._retrieval_cache.clear()
        self._answer_cache.clear()
        logger.info("✅ Local AI индекс построен: %s фрагментов", len(self._chunks))
        return len(self._chunks)

    def get_index_size(self) -> int:
        """Число фрагментов в текущем индексе (после build_index)."""
        return len(self._chunks)

    def answer(self, user_question: str) -> str | None:
        """Сгенерировать ответ на вопрос по локальной базе знаний (RAG)."""
        started_at = time.perf_counter()
        question = normalize_question_key(user_question)
        if len(question) < 3:
            return None
        self._metrics["requests_total"] += 1

        cached_answer = self._get_cached_answer(question)
        if cached_answer:
            self._metrics["cache_hits"] += 1
            self._log_metrics_if_needed(time.perf_counter() - started_at)
            return cached_answer

        retrieval = self._retrieve_facts(question)
        if not retrieval:
            self._metrics["retrieval_misses"] += 1
            self._log_quality_event("retrieval_miss", user_question, {"mode": "sync"})
            self._log_metrics_if_needed(time.perf_counter() - started_at)
            return None

        fallback_answer = self._finalize_with_llm_or_fallback(user_question, retrieval, "sync")
        self._set_cached_answer(question, fallback_answer)
        self._log_metrics_if_needed(time.perf_counter() - started_at)
        return fallback_answer

    async def answer_async(self, user_question: str) -> str | None:
        """Неблокирующая версия ответа для async-хендлеров."""
        started_at = time.perf_counter()
        question = normalize_question_key(user_question)
        if len(question) < 3:
            return None
        self._metrics["requests_total"] += 1

        async with self._inflight_lock:
            existing_future = self._inflight_answers.get(question)
            if existing_future:
                self._metrics["inflight_dedup_hits"] += 1
                return await existing_future
            loop = asyncio.get_running_loop()
            current_future: asyncio.Future[str | None] = loop.create_future()
            self._inflight_answers[question] = current_future

        try:
            cached_answer = self._get_cached_answer(question)
            if cached_answer:
                self._metrics["cache_hits"] += 1
                self._log_metrics_if_needed(time.perf_counter() - started_at)
                current_future.set_result(cached_answer)
                return cached_answer

            retrieval = self._retrieve_facts(question)
            if not retrieval:
                self._metrics["retrieval_misses"] += 1
                self._log_quality_event("retrieval_miss", user_question, {"mode": "async"})
                self._log_metrics_if_needed(time.perf_counter() - started_at)
                current_future.set_result(None)
                return None

            fallback_answer = await self._finalize_with_llm_or_fallback_async(user_question, retrieval)
            self._set_cached_answer(question, fallback_answer)
            self._log_quality_event("template_fallback", user_question, {"mode": "async"})
            self._log_metrics_if_needed(time.perf_counter() - started_at)
            current_future.set_result(fallback_answer)
            return fallback_answer
        except Exception as e:
            if not current_future.done():
                current_future.set_exception(e)
            raise
        finally:
            async with self._inflight_lock:
                self._inflight_answers.pop(question, None)

    def _retrieve_facts(self, question: str) -> RetrievalResult | None:
        """Этап retrieval: поиск релевантных фактов в индексированных JSON."""
        if not self._chunks:
            self.build_index()

        if not self._chunks:
            logger.warning("⚠️ Local AI: индекс пуст, ответ невозможен")
            return None

        cached_retrieval = self._get_cached_retrieval(question)
        if cached_retrieval:
            self._metrics["retrieval_cache_hits"] += 1
            return cached_retrieval

        detected_topic = self._detect_topic(question)
        scoped_chunks = self._filter_chunks_by_topic(detected_topic) if detected_topic else self._chunks

        scored_chunks = self._rank_chunks(question, scoped_chunks)
        min_score = 0.25 if detected_topic else 0.42
        top_chunks = [
            (chunk, score, coverage)
            for chunk, score, coverage in scored_chunks[: settings.LOCAL_AI_RETRIEVAL_TOP_K]
            if score >= min_score
        ]

        if not top_chunks:
            return None

        used_sources: list[str] = []
        fact_lines: list[str] = []

        for chunk, _score, _coverage in top_chunks:
            concise = self._make_concise_line(chunk.text)
            if concise:
                fact_lines.append(concise)
            if chunk.source not in used_sources:
                used_sources.append(chunk.source)

        if not fact_lines:
            return None

        result = RetrievalResult(
            topic_name=detected_topic,
            fact_lines=fact_lines,
            used_sources=used_sources,
            top_score=top_chunks[0][1],
            coverage_score=top_chunks[0][2],
        )
        self._set_cached_retrieval(question, result)
        return result

    def _passes_llm_confidence_gate(self, retrieval: RetrievalResult) -> bool:
        """Минимальный confidence-gate против галлюцинаций."""
        min_score = (
            settings.LOCAL_LLM_MIN_CONFIDENCE_SCORE_WITH_TOPIC
            if retrieval.topic_name
            else settings.LOCAL_LLM_MIN_CONFIDENCE_SCORE
        )
        return retrieval.top_score >= min_score and retrieval.coverage_score >= settings.LOCAL_AI_MIN_FAQ_COVERAGE

    def _facts_look_too_sparse_for_template(self, fact_lines: list[str]) -> bool:
        """Короткие/бессодержательные факты — маркированный шаблон выглядит как «общежитие №1, №2» без пользы."""
        lines = [f.strip() for f in fact_lines if f.strip()]
        if not lines:
            return True
        joined = " ".join(lines)
        if len(joined) < 160:
            return True
        avg_len = sum(len(x) for x in lines) / len(lines)
        return avg_len < 52 and len(lines) <= 5

    def _finalize_with_llm_or_fallback(
        self, user_question: str, retrieval: RetrievalResult, mode: str
    ) -> str:
        """LLM при возможности; иначе человекочитаемый fallback (не бесполезные буллеты при sparse)."""
        sparse = self._facts_look_too_sparse_for_template(retrieval.fact_lines)

        if settings.LOCAL_LLM_ENABLED:
            gate_ok = self._passes_llm_confidence_gate(retrieval)
            allow_llm = gate_ok or (
                settings.LOCAL_LLM_TRY_ON_SPARSE_CONTEXT
                and sparse
                and retrieval.topic_name is not None
                and retrieval.top_score >= settings.LOCAL_LLM_SPARSE_MIN_SCORE
            )
            if allow_llm:
                if not gate_ok:
                    logger.info(
                        "ℹ️ LLM: дополнительная попытка при разреженном контексте (score=%.3f)",
                        retrieval.top_score,
                    )
                    self._log_quality_event(
                        "llm_sparse_context_attempt",
                        user_question,
                        {"top_score": retrieval.top_score, "mode": mode},
                    )
                generated = self._generate_with_local_llm_sync(
                    user_question, retrieval, use_sparse_prompt=sparse
                )
                if generated:
                    return generated
            elif not gate_ok:
                logger.info(
                    "ℹ️ LLM confidence-gate: score=%.3f ниже порога, используем запасной ответ",
                    retrieval.top_score,
                )
                self._log_quality_event(
                    "llm_confidence_gate_skip",
                    user_question,
                    {"top_score": retrieval.top_score, "coverage": retrieval.coverage_score},
                )

        self._metrics["template_fallbacks"] += 1
        if sparse and retrieval.topic_name is not None:
            return self._compose_sparse_topic_fallback(retrieval.topic_name)
        return self._compose_answer(
            retrieval.topic_name,
            retrieval.fact_lines,
            retrieval.used_sources,
        )

    async def _finalize_with_llm_or_fallback_async(
        self, user_question: str, retrieval: RetrievalResult
    ) -> str:
        sparse = self._facts_look_too_sparse_for_template(retrieval.fact_lines)

        if settings.LOCAL_LLM_ENABLED:
            gate_ok = self._passes_llm_confidence_gate(retrieval)
            allow_llm = gate_ok or (
                settings.LOCAL_LLM_TRY_ON_SPARSE_CONTEXT
                and sparse
                and retrieval.topic_name is not None
                and retrieval.top_score >= settings.LOCAL_LLM_SPARSE_MIN_SCORE
            )
            if allow_llm:
                if not gate_ok:
                    logger.info(
                        "ℹ️ LLM: дополнительная попытка при разреженном контексте (score=%.3f)",
                        retrieval.top_score,
                    )
                    self._log_quality_event(
                        "llm_sparse_context_attempt",
                        user_question,
                        {"top_score": retrieval.top_score, "mode": "async"},
                    )
                generated = await self._generate_with_local_llm_async(
                    user_question, retrieval, use_sparse_prompt=sparse
                )
                if generated:
                    return generated
            elif not gate_ok:
                logger.info(
                    "ℹ️ LLM confidence-gate: score=%.3f ниже порога, используем запасной ответ",
                    retrieval.top_score,
                )
                self._log_quality_event(
                    "llm_confidence_gate_skip",
                    user_question,
                    {"top_score": retrieval.top_score, "coverage": retrieval.coverage_score},
                )

        self._metrics["template_fallbacks"] += 1
        if sparse and retrieval.topic_name is not None:
            return self._compose_sparse_topic_fallback(retrieval.topic_name)
        return self._compose_answer(
            retrieval.topic_name,
            retrieval.fact_lines,
            retrieval.used_sources,
        )

    def _compose_sparse_topic_fallback(self, topic_name: str | None) -> str:
        """Если в RAG только обрывки — не показываем маркеры из одних названий."""
        site = "https://mospolytech.ru/"
        base = (
            "В базе бота сейчас только короткие фрагменты по этой теме — без полного официального текста.\n\n"
            f"Актуальные правила и контакты смотри на сайте: {site}\n\n"
        )
        hints = {
            "dormitories": "Напиши, пожалуйста: иногородний ли ты, форма обучения (очная/заочная) — "
            "подскажу, какой раздел на сайте открыть.",
            "scholarships": "Уточни курс и тип выплаты (академическая, социальная и т.д.) — отвечу точнее.",
            "mfc": "Напиши, какая именно справка или услуга нужна — наведу на нужную страницу МФЦ.",
            "schedule": "Уточни группу или направление — подскажу, где в личном кабинете смотреть расписание.",
        }
        return base + hints.get(topic_name, "Переформулируй вопрос или выбери раздел в меню бота.")

    def _extract_chunks_from_file(self, json_file: Path) -> list[KnowledgeChunk]:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:
            logger.warning("⚠️ Local AI: не удалось прочитать %s: %s", json_file, e)
            return []

        chunks: list[KnowledgeChunk] = []
        self._walk_json(payload, json_file, "$", chunks)
        return chunks

    def _extract_chunks_from_txt_file(self, text_file: Path) -> list[KnowledgeChunk]:
        try:
            text = text_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("⚠️ Local AI: не удалось прочитать %s: %s", text_file, e)
            return []

        normalized = normalize_text(text)
        if len(normalized) < 8:
            return []

        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
        chunks: list[KnowledgeChunk] = []
        for index, paragraph in enumerate(paragraphs, start=1):
            if len(paragraph) < 8:
                continue
            chunks.append(
                KnowledgeChunk(
                    source=text_file.name,
                    path=f"$.paragraph[{index}]",
                    text=paragraph,
                )
            )
        return chunks

    def _walk_json(
        self,
        value: object,
        source_file: Path,
        current_path: str,
        chunks: list[KnowledgeChunk],
    ) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                child_path = f"{current_path}.{key}"
                self._walk_json(item, source_file, child_path, chunks)
            return

        if isinstance(value, list):
            for index, item in enumerate(value):
                child_path = f"{current_path}[{index}]"
                self._walk_json(item, source_file, child_path, chunks)
            return

        if value is None:
            return

        text = str(value).strip()
        if len(text) < 8:
            return

        normalized = normalize_text(text)
        if not normalized:
            return

        chunks.append(
            KnowledgeChunk(
                source=source_file.name,
                path=current_path,
                text=normalized,
            )
        )

    def _rank_chunks(
        self,
        question: str,
        candidate_chunks: list[KnowledgeChunk],
    ) -> list[tuple[KnowledgeChunk, float, float]]:
        question_tokens = tokenize(question)
        scored: list[tuple[KnowledgeChunk, float, float]] = []
        question_embedding = self._get_embedding(question) if settings.LOCAL_EMBEDDINGS_ENABLED else None

        for chunk in candidate_chunks:
            chunk_tokens = tokenize(chunk.text)
            if not chunk_tokens:
                continue

            overlap = len(question_tokens & chunk_tokens) / max(len(question_tokens), 1)
            fuzzy = difflib.SequenceMatcher(None, question, chunk.text).ratio()
            embedding_similarity = 0.0
            if question_embedding:
                chunk_embedding = chunk.embedding or self._get_embedding(chunk.text)
                if chunk_embedding:
                    chunk.embedding = chunk_embedding
                    embedding_similarity = self._cosine_similarity(question_embedding, chunk_embedding)

            lexical_score = overlap * 0.75 + fuzzy * 0.25
            if question_embedding and embedding_similarity > 0:
                score = (
                    lexical_score * (1 - settings.LOCAL_EMBEDDINGS_WEIGHT)
                    + embedding_similarity * settings.LOCAL_EMBEDDINGS_WEIGHT
                )
            else:
                score = lexical_score
            if score > 0:
                scored.append((chunk, score, overlap))

        scored.sort(key=lambda item: (item[1], item[2]), reverse=True)
        return scored

    def _get_embedding(self, text: str) -> list[float] | None:
        cache_key = normalize_text(text)
        cached = self._embedding_cache.get(cache_key)
        if cached:
            return cached
        try:
            response = requests.post(
                settings.LOCAL_EMBEDDINGS_API_URL,
                json={"model": settings.LOCAL_EMBEDDINGS_MODEL, "prompt": text},
                timeout=settings.LOCAL_LLM_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            vector = payload.get("embedding")
            if not isinstance(vector, list) or not vector:
                return None
            normalized_vector = [float(v) for v in vector]
            self._embedding_cache[cache_key] = normalized_vector
            return normalized_vector
        except Exception:
            return None

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _detect_topic(self, question: str) -> str | None:
        question_text = normalize_text(question)
        best_topic = None
        best_score = 0

        for rule in self.TOPIC_RULES:
            score = 0
            for keyword in rule.keywords:
                if keyword in question_text:
                    score += 1
            if score > best_score:
                best_score = score
                best_topic = rule.name

        return best_topic if best_score > 0 else None

    def _chunk_matches_topic(self, chunk: KnowledgeChunk, topic_name: str) -> bool:
        source_signature = normalize_text(f"{chunk.source} {chunk.path}")
        for rule in self.TOPIC_RULES:
            if rule.name != topic_name:
                continue
            return any(hint in source_signature for hint in rule.source_hints)
        return False

    def _filter_chunks_by_topic(self, topic_name: str) -> list[KnowledgeChunk]:
        scoped = [chunk for chunk in self._chunks if self._chunk_matches_topic(chunk, topic_name)]
        return scoped if scoped else self._chunks

    def _make_concise_line(self, text: str) -> str:
        line = text.strip()
        max_chars = settings.LOCAL_AI_MAX_FACT_LINE_CHARS
        if len(line) > max_chars:
            line = f"{line[: max_chars - 3]}..."
        return line

    def _get_cached_answer(self, question_key: str) -> str | None:
        entry = self._answer_cache.get(question_key)
        if not entry:
            return None
        if entry.expires_at <= time.time():
            self._answer_cache.pop(question_key, None)
            return None
        return entry.answer_text

    def _set_cached_answer(self, question_key: str, answer_text: str) -> None:
        self._prune_cache_if_needed()
        expires_at = time.time() + settings.LOCAL_AI_CACHE_TTL_SEC
        self._answer_cache[question_key] = CacheEntry(answer_text=answer_text, expires_at=expires_at)
        self._prune_cache_if_needed()

    def _get_cached_retrieval(self, question_key: str) -> RetrievalResult | None:
        entry = self._retrieval_cache.get(question_key)
        if not entry:
            return None
        if entry.expires_at <= time.time():
            self._retrieval_cache.pop(question_key, None)
            return None
        return copy.deepcopy(entry.retrieval)

    def _set_cached_retrieval(self, question_key: str, retrieval: RetrievalResult) -> None:
        self._prune_retrieval_cache_if_needed()
        expires_at = time.time() + settings.LOCAL_AI_RETRIEVAL_CACHE_TTL_SEC
        self._retrieval_cache[question_key] = RetrievalCacheEntry(
            retrieval=copy.deepcopy(retrieval), expires_at=expires_at
        )
        self._prune_retrieval_cache_if_needed()

    def _prune_retrieval_cache_if_needed(self) -> None:
        now = time.time()
        expired_keys = [key for key, entry in self._retrieval_cache.items() if entry.expires_at <= now]
        for key in expired_keys:
            self._retrieval_cache.pop(key, None)

        overflow = len(self._retrieval_cache) - settings.LOCAL_AI_RETRIEVAL_CACHE_MAX_SIZE
        if overflow > 0:
            keys_to_drop = list(self._retrieval_cache.keys())[:overflow]
            for key in keys_to_drop:
                self._retrieval_cache.pop(key, None)

    def _prune_cache_if_needed(self) -> None:
        now = time.time()
        expired_keys = [key for key, entry in self._answer_cache.items() if entry.expires_at <= now]
        for key in expired_keys:
            self._answer_cache.pop(key, None)

        overflow = len(self._answer_cache) - settings.LOCAL_AI_CACHE_MAX_SIZE
        if overflow > 0:
            keys_to_drop = list(self._answer_cache.keys())[:overflow]
            for key in keys_to_drop:
                self._answer_cache.pop(key, None)

    def _log_metrics_if_needed(self, elapsed_sec: float) -> None:
        if self._metrics["requests_total"] % settings.LOCAL_AI_METRICS_LOG_EVERY != 0:
            return
        logger.info(
            "📊 Local AI metrics: total=%s, cache_hits=%s, retrieval_cache_hits=%s, retrieval_misses=%s, "
            "llm_success=%s, llm_failures=%s, template_fallbacks=%s, inflight_dedup_hits=%s, "
            "circuit_open_skips=%s, high_load_activations=%s, llm_mode=%s, last_latency_ms=%s",
            self._metrics["requests_total"],
            self._metrics["cache_hits"],
            self._metrics["retrieval_cache_hits"],
            self._metrics["retrieval_misses"],
            self._metrics["llm_success"],
            self._metrics["llm_failures"],
            self._metrics["template_fallbacks"],
            self._metrics["inflight_dedup_hits"],
            self._metrics["circuit_open_skips"],
            self._metrics["high_load_activations"],
            self._llm_last_mode,
            int(elapsed_sec * 1000),
        )

    def _log_quality_event(self, event_type: str, user_question: str, details: dict[str, object]) -> None:
        """Записать кейс для weekly review проблемных ответов."""
        try:
            review_dir = PROJECT_ROOT / settings.QUALITY_REVIEW_LOG_DIR
            review_dir.mkdir(parents=True, exist_ok=True)
            year, week, _ = datetime.now(timezone.utc).isocalendar()
            review_file = review_dir / f"review-{year}-W{week:02d}.jsonl"
            payload = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "event_type": event_type,
                "question": user_question.strip(),
                "details": details,
            }
            with open(review_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            # Не ломаем основной пайплайн из-за логирования качества.
            return

    def note_quality_event(self, event_type: str, user_question: str, details: dict[str, object] | None = None) -> None:
        """Публичная запись кейса для weekly review."""
        self._log_quality_event(event_type, user_question, details or {})

    def _compose_answer(
        self,
        topic_name: str | None,
        fact_lines: list[str],
        used_sources: list[str],
    ) -> str:
        topic_titles = {
            "scholarships": "стипендиям",
            "dormitories": "общежитиям",
            "mfc": "услугам МФЦ",
            "schedule": "расписанию",
        }

        title_part = topic_titles.get(topic_name, "твоему вопросу")
        opening = f"🤖 Вот что удалось найти по {title_part}:"

        unique_facts: list[str] = []
        for fact in fact_lines:
            if fact not in unique_facts:
                unique_facts.append(fact)

        bullets = "\n".join(f"• {fact}" for fact in unique_facts[:3])
        recommendation = (
            "Если понадобится, могу уточнить ответ под твою ситуацию "
            "(курс, форма обучения, льготная категория и т.д.)."
        )
        site_hint = (
            "Актуальные детали и контакты также смотри на официальном сайте: https://mospolytech.ru/"
        )
        return f"{opening}\n\n{bullets}\n\n{recommendation}\n{site_hint}"

    def _select_context_lines_for_llm(self, fact_lines: list[str], *, high_load: bool = False) -> list[str]:
        """
        Сжать контекст под лимит модели:
        - оставляем порядок по релевантности (как из retrieval),
        - убираем дубли,
        - ограничиваем общий объём LOCAL_AI_LLM_MAX_CONTEXT_CHARS.
        """
        selected: list[str] = []
        max_chars = settings.LOCAL_AI_LLM_MAX_CONTEXT_CHARS
        if high_load and settings.LOCAL_LLM_ADAPTIVE_LOAD_ENABLED:
            reduced_limit = int(max_chars * settings.LOCAL_LLM_HIGH_LOAD_CONTEXT_FACTOR)
            max_chars = max(800, reduced_limit)
        total_chars = 0
        for line in fact_lines:
            clean = line.strip()
            if not clean or clean in selected:
                continue
            projected = total_chars + len(clean) + 3  # "- " + "\n"
            if selected and projected > max_chars:
                break
            selected.append(clean)
            total_chars = projected
        return selected

    def _build_llm_prompt(
        self, user_question: str, retrieval: RetrievalResult, *, high_load: bool = False
    ) -> str:
        topic_titles = {
            "scholarships": "стипендии",
            "dormitories": "общежития",
            "mfc": "услуги МФЦ",
            "schedule": "расписание",
        }
        topic_text = topic_titles.get(retrieval.topic_name, "общие вопросы")
        context_lines_for_llm = self._select_context_lines_for_llm(
            retrieval.fact_lines,
            high_load=high_load,
        )
        context_lines = "\n".join(f"- {line}" for line in context_lines_for_llm)
        sources_text = ", ".join(retrieval.used_sources[:4])

        return (
            "Ты помощник Telegram-бота МосПолитеха.\n"
            "Ответь пользователю ТОЛЬКО на основе контекста ниже.\n"
            "Если данных недостаточно, прямо скажи, что информации недостаточно, "
            "и предложи уточнить вопрос.\n"
            "Пиши дружелюбно, на русском языке.\n"
            "Если вопрос про процесс, условия, документы, сроки или действия пользователя — "
            "дай подробный структурированный ответ.\n"
            "Если вопрос простой фактологический — достаточно 2-4 предложений.\n"
            "Не выдумывай данные, которых нет в контексте.\n\n"
            f"Тема: {topic_text}\n"
            f"Вопрос пользователя: {user_question.strip()}\n\n"
            "Контекст:\n"
            f"{context_lines}\n\n"
            f"Источники контекста: {sources_text}\n\n"
            "Сделай ответ визуально аккуратным для Telegram: короткие абзацы и/или маркеры, без служебных заголовков.\n"
            "Не используй нумерованные шаблоны вида '1) ... 2) ... 3) ...'.\n"
            "Не добавляй строку вида 'Источник: ...'.\n"
            "Если рекомендуешь посмотреть информацию на официальном сайте, обязательно укажи ссылку https://mospolytech.ru/.\n"
            "Сформируй финальный ответ для пользователя без служебных комментариев."
        )

    def _build_llm_prompt_sparse_context(
        self, user_question: str, retrieval: RetrievalResult, *, high_load: bool = False
    ) -> str:
        """Промпт при слабом RAG: меньше «выдуманных шагов», честнее про нехватку данных."""
        topic_titles = {
            "scholarships": "стипендии",
            "dormitories": "общежития",
            "mfc": "услуги МФЦ",
            "schedule": "расписание",
        }
        topic_text = topic_titles.get(retrieval.topic_name, "общие вопросы")
        context_lines_for_llm = self._select_context_lines_for_llm(
            retrieval.fact_lines,
            high_load=high_load,
        )
        context_lines = "\n".join(f"- {line}" for line in context_lines_for_llm)
        sources_text = ", ".join(retrieval.used_sources[:4])

        return (
            "Ты помощник Telegram-бота МосПолитеха.\n"
            "Контекст из базы ОЧЕНЬ краткий или состоит из отдельных строк (например только названия).\n"
            "Правила:\n"
            "- Не выдумывай конкретные шаги, сроки, суммы, перечни документов или процедуры, которых нет в контексте.\n"
            "- Если контекста недостаточно для пошаговой инструкции — честно скажи об этом и направь на официальный сайт "
            "https://mospolytech.ru/\n"
            "- Можно кратко пересказать то, что явно есть в контексте (1–3 коротких предложения).\n"
            "- Пиши по-русски, дружелюбно, без служебных заголовков.\n"
            "- Запрещены нумерованные списки вида «1) … 2) …».\n\n"
            f"Тема: {topic_text}\n"
            f"Вопрос пользователя: {user_question.strip()}\n\n"
            "Фрагменты контекста:\n"
            f"{context_lines}\n\n"
            f"Источники: {sources_text}\n\n"
            "Сформируй ответ для Telegram одним-двумя абзацами плюс при необходимости маркеры «•». "
            "Если упоминаешь официальный сайт — обязательно https://mospolytech.ru/"
        )

    def _ensure_official_site_link(self, text: str) -> str:
        """Добавить ссылку на официальный сайт, если он упомянут без URL."""
        normalized = normalize_text(text)
        if "официальн" in normalized and "mospolytech.ru" not in normalized:
            return f"{text}\n\nПодробнее на официальном сайте: https://mospolytech.ru/"
        return text

    def _is_complex_question(self, user_question: str) -> bool:
        """Эвристика: процессные/длинные вопросы роутим на более сильную модель."""
        normalized = normalize_text(user_question)
        question_tokens = tokenize(normalized)
        if len(question_tokens) >= settings.LOCAL_LLM_COMPLEX_MIN_TOKENS:
            return True
        process_hints = (
            "как",
            "каким образом",
            "порядок",
            "этап",
            "шаг",
            "документ",
            "список документов",
            "услови",
            "требован",
            "срок",
            "когда",
            "куда",
        )
        return any(hint in normalized for hint in process_hints)

    def _resolve_llm_models_for_question(self, user_question: str) -> list[str]:
        """
        Выбрать каскад моделей:
        - сложный вопрос -> LOCAL_LLM_COMPLEX_MODELS
        - простой вопрос -> LOCAL_LLM_SIMPLE_MODELS
        - затем дополняем общим каскадом LOCAL_LLM_MODELS без дублей.
        """
        primary_models = (
            settings.local_llm_complex_models_list
            if self._is_complex_question(user_question)
            else settings.local_llm_simple_models_list
        )
        fallback_models = settings.local_llm_models_list
        resolved: list[str] = []
        for model in [*primary_models, *fallback_models]:
            if model and model not in resolved:
                resolved.append(model)
        if not resolved and settings.LOCAL_LLM_MODEL:
            resolved.append(settings.LOCAL_LLM_MODEL)
        return resolved

    async def _is_high_load_now(self) -> bool:
        if not settings.LOCAL_LLM_ADAPTIVE_LOAD_ENABLED:
            return False
        async with self._llm_load_lock:
            return (
                self._llm_waiting_requests >= settings.LOCAL_LLM_HIGH_LOAD_WAITERS_THRESHOLD
                or self._llm_inflight_requests >= settings.LOCAL_LLM_HIGH_LOAD_INFLIGHT_THRESHOLD
            )

    async def _generate_with_local_llm_async(
        self,
        user_question: str,
        retrieval: RetrievalResult,
        *,
        use_sparse_prompt: bool = False,
    ) -> str | None:
        """Неблокирующий generation: network-вызов уходит в thread pool."""
        if not self._llm_circuit_allows_request():
            self._metrics["circuit_open_skips"] += 1
            self._log_quality_event("llm_circuit_open", user_question, {"mode": "async"})
            return None
        high_load = await self._is_high_load_now()
        if high_load:
            logger.info("⚡ High-load режим LLM: применяю ускоренную генерацию")
            self._metrics["high_load_activations"] += 1
        self._llm_last_mode = "high_load" if high_load else "normal"

        async with self._llm_load_lock:
            self._llm_waiting_requests += 1
        await self._llm_semaphore.acquire()
        try:
            async with self._llm_load_lock:
                self._llm_waiting_requests = max(0, self._llm_waiting_requests - 1)
                self._llm_inflight_requests += 1
            return await asyncio.to_thread(
                self._generate_with_local_llm_sync,
                user_question,
                retrieval,
                use_sparse_prompt,
                high_load,
            )
        finally:
            async with self._llm_load_lock:
                self._llm_inflight_requests = max(0, self._llm_inflight_requests - 1)
            self._llm_semaphore.release()

    def _generate_with_local_llm_sync(
        self,
        user_question: str,
        retrieval: RetrievalResult,
        use_sparse_prompt: bool = False,
        high_load: bool = False,
    ) -> str | None:
        """Синхронный generation: HTTP-запрос к локальной LLM (например, Ollama)."""
        if not self._llm_circuit_allows_request():
            self._metrics["circuit_open_skips"] += 1
            self._log_quality_event("llm_circuit_open", user_question, {"mode": "sync"})
            return None

        if use_sparse_prompt:
            prompt = self._build_llm_prompt_sparse_context(
                user_question,
                retrieval,
                high_load=high_load,
            )
        else:
            prompt = self._build_llm_prompt(
                user_question,
                retrieval,
                high_load=high_load,
            )

        last_error: str | None = None
        if high_load and settings.LOCAL_LLM_ADAPTIVE_LOAD_ENABLED and settings.local_llm_simple_models_list:
            self._llm_last_mode = "high_load"
            llm_models = [*settings.local_llm_simple_models_list, *settings.local_llm_models_list]
            llm_models = list(dict.fromkeys(llm_models))
        else:
            self._llm_last_mode = "normal"
            llm_models = self._resolve_llm_models_for_question(user_question)
        if not llm_models:
            llm_models = [settings.LOCAL_LLM_MODEL]

        for llm_model in llm_models:
            payload = {
                "model": llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": settings.LOCAL_LLM_TEMPERATURE,
                    "num_predict": (
                        settings.LOCAL_LLM_HIGH_LOAD_MAX_TOKENS
                        if high_load and settings.LOCAL_LLM_ADAPTIVE_LOAD_ENABLED
                        else settings.LOCAL_LLM_MAX_TOKENS
                    ),
                },
            }
            try:
                response = requests.post(
                    settings.LOCAL_LLM_API_URL,
                    json=payload,
                    timeout=settings.LOCAL_LLM_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                llm_text = data.get("response", "").strip()
                if not llm_text:
                    last_error = f"empty_response:{llm_model}"
                    self._register_llm_failure()
                    continue

                self._register_llm_success()
                logger.info("✅ Local LLM ответил моделью: %s", llm_model)
                return self._ensure_official_site_link(llm_text)
            except Exception as e:
                last_error = str(e)[:200]
                self._register_llm_failure()
                logger.warning("⚠️ Local LLM model '%s' недоступна: %s", llm_model, e)

        logger.warning("⚠️ Local LLM недоступна, fallback на шаблонный ответ")
        self._log_quality_event(
            "llm_request_failed",
            user_question,
            {"error": last_error or "all_models_failed", "models": llm_models},
        )
        return None

    def _llm_circuit_allows_request(self) -> bool:
        return time.time() >= self._llm_circuit_open_until

    def _register_llm_success(self) -> None:
        self._llm_circuit_failures = 0
        self._llm_circuit_open_until = 0.0
        self._metrics["llm_success"] += 1

    def _register_llm_failure(self) -> None:
        self._metrics["llm_failures"] += 1
        self._llm_circuit_failures += 1
        if self._llm_circuit_failures >= settings.LOCAL_LLM_CIRCUIT_FAILURES:
            self._llm_circuit_open_until = time.time() + settings.LOCAL_LLM_CIRCUIT_COOLDOWN_SEC
            self._llm_circuit_failures = 0


local_ai_service: LocalAIService | None = None


def _warmup_local_llm() -> None:
    """Короткий запрос к локальной LLM при старте, чтобы снизить latency первого ответа пользователя."""
    if not settings.LOCAL_LLM_ENABLED or not settings.LOCAL_LLM_WARMUP_ENABLED:
        return
    llm_models = settings.local_llm_models_list
    if not llm_models:
        llm_models = [settings.LOCAL_LLM_MODEL]

    for llm_model in llm_models:
        payload = {
            "model": llm_model,
            "prompt": "Ответь одним словом: ок.",
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 6},
        }
        try:
            response = requests.post(
                settings.LOCAL_LLM_API_URL,
                json=payload,
                timeout=settings.LOCAL_LLM_WARMUP_TIMEOUT,
            )
            response.raise_for_status()
            logger.info("✅ Local LLM warmup: запрос к %s выполнен", llm_model)
            return
        except Exception as e:
            logger.warning("⚠️ Local LLM warmup модели '%s' не удался: %s", llm_model, e)

    logger.warning(
        "⚠️ Local LLM warmup не удался ни для одной модели "
        "(первый пользовательский запрос может быть медленнее)"
    )


def init_local_ai_service() -> LocalAIService:
    """Инициализировать и прогреть локальный AI-сервис."""
    global local_ai_service
    if local_ai_service is None:
        local_ai_service = LocalAIService()
    local_ai_service.build_index()
    _warmup_local_llm()
    return local_ai_service


def get_local_ai_service() -> LocalAIService:
    """Получить экземпляр локального AI-сервиса."""
    global local_ai_service
    if local_ai_service is None:
        local_ai_service = LocalAIService()
    return local_ai_service
