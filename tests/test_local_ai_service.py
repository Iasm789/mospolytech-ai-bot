import json

from config.settings import settings
from services.local_ai_service import LocalAIService, RetrievalResult


def test_local_ai_get_index_size(tmp_path):
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "a.json").write_text(json.dumps({"x": "y" * 20}, ensure_ascii=False), encoding="utf-8")
    service = LocalAIService(data_dirs=(data_dir,))
    assert service.get_index_size() == 0
    n = service.build_index()
    assert service.get_index_size() == n
    assert n > 0


def test_local_ai_builds_index_from_json(tmp_path):
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / "scholarships.json"
    data_file.write_text(
        json.dumps(
            {
                "categories": [
                    {
                        "name": "Социальные",
                        "scholarships": [{"name": "Социальная стипендия", "amount": "3500 руб."}],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    chunks_count = service.build_index()

    assert chunks_count > 0


def test_local_ai_builds_index_from_txt(tmp_path):
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "university_info.txt").write_text(
        "В МосПолитехе есть проектная деятельность.\n\nСтуденты могут участвовать в хакатонах.",
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    chunks_count = service.build_index()

    assert chunks_count > 0

    answer = service.answer("Есть ли в вузе проектная деятельность?")
    assert answer is not None
    assert "проектная деятельность" in answer.lower()
    assert "Источник:" not in answer


def test_local_ai_returns_answer_when_context_matches(tmp_path):
    settings.LOCAL_LLM_ENABLED = False
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / "dormitories.json"
    data_file.write_text(
        json.dumps(
            {
                "general_info": {
                    "title": "Общежития",
                    # Длинный текст — не «разреженный» факт, чтобы проверять классический шаблон с буллетами
                    "description": (
                        "Заселение доступно для иногородних студентов после приказа. "
                        * 10
                    ),
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    answer = service.answer("Как происходит заселение в общежитие для иногородних?")

    assert answer is not None
    assert "вот что удалось найти" in answer.lower()
    assert "заселение" in answer.lower()
    assert "Источник:" not in answer


def test_local_ai_returns_none_for_irrelevant_question(tmp_path):
    settings.LOCAL_LLM_ENABLED = False
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_file = data_dir / "events.json"
    data_file.write_text(
        json.dumps({"events": [{"name": "День карьеры", "description": "Ярмарка вакансий"}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    answer = service.answer("Какая погода завтра в Москве?")

    assert answer is None


def test_local_ai_uses_topic_routing_for_schedule(tmp_path):
    settings.LOCAL_LLM_ENABLED = False
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "schedule_data.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "text": (
                            "Расписание занятий и экзаменов смотри в личном кабинете студента на портале. "
                            "Актуальные изменения появляются в личном кабинете после утверждения. "
                        )
                        * 4
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (data_dir / "scholarships.json").write_text(
        json.dumps(
            {"categories": [{"name": "Социальная стипендия", "amount": "3000"}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    answer = service.answer("Где посмотреть расписание на неделю?")

    assert answer is not None
    assert "расписан" in answer.lower()
    assert "личном кабинете" in answer.lower()
    assert "Источник:" not in answer


def test_local_ai_uses_llm_generation_when_enabled(tmp_path, monkeypatch):
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "mfc_services.json").write_text(
        json.dumps(
            {"services": [{"name": "Справка об обучении", "details": "Выдается в МФЦ"}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Можно оформить справку об обучении через МФЦ университета."}

    def fake_post(url, json, timeout):  # noqa: A002
        assert "model" in json
        assert "prompt" in json
        return DummyResponse()

    monkeypatch.setattr("services.local_ai_service.requests.post", fake_post)
    monkeypatch.setattr(settings, "LOCAL_LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODEL", "qwen2.5:3b")
    monkeypatch.setattr(settings, "LOCAL_LLM_API_URL", "http://127.0.0.1:11434/api/generate")
    monkeypatch.setattr(settings, "LOCAL_LLM_TIMEOUT", 5)

    service = LocalAIService(data_dirs=(data_dir,))
    answer = service.answer("Где получить справку об обучении?")

    assert answer is not None
    assert "через МФЦ" in answer
    assert "Источник:" not in answer


def test_local_ai_falls_back_to_next_llm_model(tmp_path, monkeypatch):
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "mfc_services.json").write_text(
        json.dumps(
            {"services": [{"name": "Справка об обучении", "details": "Выдается в МФЦ"}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Ответ со второй модели fallback."}

    calls = {"models": []}

    def fake_post(url, json, timeout):  # noqa: A002
        model = json.get("model")
        calls["models"].append(model)
        if model == "qwen2.5:7b":
            raise RuntimeError("primary model unavailable")
        return DummyResponse()

    monkeypatch.setattr("services.local_ai_service.requests.post", fake_post)
    monkeypatch.setattr(settings, "LOCAL_LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODEL", "qwen2.5:7b")
    monkeypatch.setattr(settings, "LOCAL_LLM_MODELS", "qwen2.5:7b,qwen2.5:3b")
    monkeypatch.setattr(settings, "LOCAL_LLM_API_URL", "http://127.0.0.1:11434/api/generate")
    monkeypatch.setattr(settings, "LOCAL_LLM_TIMEOUT", 5)

    service = LocalAIService(data_dirs=(data_dir,))
    answer = service.answer("Где получить справку об обучении?")

    assert answer is not None
    assert "fallback" in answer.lower()
    assert calls["models"][:2] == ["qwen2.5:7b", "qwen2.5:3b"]


def test_local_ai_routes_simple_question_to_simple_models(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Короткий ответ для простого вопроса."}

    calls = {"models": []}

    def fake_post(url, json, timeout):  # noqa: A002
        calls["models"].append(json.get("model"))
        return DummyResponse()

    monkeypatch.setattr("services.local_ai_service.requests.post", fake_post)
    monkeypatch.setattr(settings, "LOCAL_LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODELS", "qwen2.5:7b")
    monkeypatch.setattr(settings, "LOCAL_LLM_SIMPLE_MODELS", "qwen2.5:3b")
    monkeypatch.setattr(settings, "LOCAL_LLM_COMPLEX_MODELS", "qwen2.5:14b")
    monkeypatch.setattr(settings, "LOCAL_LLM_COMPLEX_MIN_TOKENS", 12)

    service = LocalAIService(data_dirs=())
    retrieval = RetrievalResult(
        topic_name="mfc",
        fact_lines=["Справка об обучении выдается в МФЦ университета."],
        used_sources=["mfc_services.json"],
        top_score=0.9,
        coverage_score=0.9,
    )
    answer = service._generate_with_local_llm_sync("Где получить справку?", retrieval)

    assert answer is not None
    assert calls["models"][0] == "qwen2.5:3b"


def test_local_ai_routes_complex_question_to_complex_models(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Подробный ответ для сложного вопроса."}

    calls = {"models": []}

    def fake_post(url, json, timeout):  # noqa: A002
        calls["models"].append(json.get("model"))
        return DummyResponse()

    monkeypatch.setattr("services.local_ai_service.requests.post", fake_post)
    monkeypatch.setattr(settings, "LOCAL_LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODELS", "qwen2.5:7b")
    monkeypatch.setattr(settings, "LOCAL_LLM_SIMPLE_MODELS", "qwen2.5:3b")
    monkeypatch.setattr(settings, "LOCAL_LLM_COMPLEX_MODELS", "qwen2.5:14b")
    monkeypatch.setattr(settings, "LOCAL_LLM_COMPLEX_MIN_TOKENS", 6)

    service = LocalAIService(data_dirs=())
    retrieval = RetrievalResult(
        topic_name="dormitories",
        fact_lines=["Заселение доступно для иногородних студентов после подачи документов."],
        used_sources=["dormitories.json"],
        top_score=0.9,
        coverage_score=0.9,
    )
    answer = service._generate_with_local_llm_sync(
        "Какие документы и в какие сроки нужно подать для заселения в общежитие?",
        retrieval,
    )

    assert answer is not None
    assert calls["models"][0] == "qwen2.5:14b"


def test_select_context_lines_for_llm_respects_char_limit(monkeypatch):
    service = LocalAIService(data_dirs=())
    monkeypatch.setattr(settings, "LOCAL_AI_LLM_MAX_CONTEXT_CHARS", 70)
    lines = [
        "Первая релевантная строка с важным контекстом.",
        "Вторая релевантная строка, которая может не влезть.",
        "Третья строка.",
    ]

    selected = service._select_context_lines_for_llm(lines)

    assert len(selected) >= 1
    assert selected[0].startswith("Первая релевантная")
    assert sum(len(line) + 3 for line in selected) <= settings.LOCAL_AI_LLM_MAX_CONTEXT_CHARS + 3


def test_high_load_mode_prefers_simple_models_and_lower_token_budget(monkeypatch):
    service = LocalAIService(data_dirs=())
    retrieval = RetrievalResult(
        topic_name="dormitories",
        fact_lines=["Заселение доступно для иногородних студентов после подачи документов."],
        used_sources=["dormitories.json"],
        top_score=0.9,
        coverage_score=0.9,
    )
    calls = {"models": [], "num_predict": []}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Ответ в high-load режиме."}

    def fake_post(url, json, timeout):  # noqa: A002
        calls["models"].append(json.get("model"))
        calls["num_predict"].append(json.get("options", {}).get("num_predict"))
        return DummyResponse()

    monkeypatch.setattr("services.local_ai_service.requests.post", fake_post)
    monkeypatch.setattr(settings, "LOCAL_LLM_ADAPTIVE_LOAD_ENABLED", True)
    monkeypatch.setattr(settings, "LOCAL_LLM_MODELS", "qwen2.5:7b")
    monkeypatch.setattr(settings, "LOCAL_LLM_SIMPLE_MODELS", "qwen2.5:3b")
    monkeypatch.setattr(settings, "LOCAL_LLM_COMPLEX_MODELS", "qwen2.5:14b")
    monkeypatch.setattr(settings, "LOCAL_LLM_HIGH_LOAD_MAX_TOKENS", 230)

    answer = service._generate_with_local_llm_sync(
        "Какие документы и в какие сроки нужны для заселения?",
        retrieval,
        high_load=True,
    )

    assert answer is not None
    assert calls["models"][0] == "qwen2.5:3b"
    assert calls["num_predict"][0] == 230
    assert service._llm_last_mode == "high_load"


def test_local_ai_cache_hit_skips_second_retrieval(tmp_path, monkeypatch):
    settings.LOCAL_LLM_ENABLED = False
    settings.LOCAL_AI_CACHE_TTL_SEC = 300
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "dormitories.json").write_text(
        json.dumps(
            {"general_info": {"description": "Заселение доступно для иногородних студентов."}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    call_counter = {"count": 0}
    original_retrieve = service._retrieve_facts

    def wrapped_retrieve(question):
        call_counter["count"] += 1
        return original_retrieve(question)

    monkeypatch.setattr(service, "_retrieve_facts", wrapped_retrieve)

    question = "Как происходит заселение в общежитие для иногородних?"
    answer_first = service.answer(question)
    answer_second = service.answer(question)

    assert answer_first is not None
    assert answer_second == answer_first
    assert call_counter["count"] == 1


def test_local_ai_retrieval_cache_skips_rank_when_answer_not_cached(tmp_path, monkeypatch):
    """При промахе кэша ответа повторный запрос берёт retrieval из кэша — ранжирование не повторяется."""
    settings.LOCAL_LLM_ENABLED = False
    settings.LOCAL_AI_RETRIEVAL_CACHE_TTL_SEC = 600
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "dormitories.json").write_text(
        json.dumps(
            {"general_info": {"description": "Заселение доступно для иногородних студентов."}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))
    rank_calls = {"n": 0}
    original_rank = service._rank_chunks

    def wrapped_rank(question: str, candidate_chunks):
        rank_calls["n"] += 1
        return original_rank(question, candidate_chunks)

    monkeypatch.setattr(service, "_rank_chunks", wrapped_rank)
    monkeypatch.setattr(service, "_get_cached_answer", lambda q: None)
    monkeypatch.setattr(service, "_set_cached_answer", lambda q, t: None)

    question = "Как происходит заселение в общежитие для иногородних?"
    service.answer(question)
    service.answer(question)

    assert rank_calls["n"] == 1


def test_local_ai_cache_expires_by_ttl(tmp_path, monkeypatch):
    settings.LOCAL_LLM_ENABLED = False
    settings.LOCAL_AI_CACHE_TTL_SEC = 1
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "schedule_data.json").write_text(
        json.dumps(
            {"items": [{"text": "Расписание доступно в личном кабинете."}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    now = {"value": 1_000_000}
    monkeypatch.setattr("services.local_ai_service.time.time", lambda: now["value"])

    service = LocalAIService(data_dirs=(data_dir,))
    call_counter = {"count": 0}
    original_retrieve = service._retrieve_facts

    def wrapped_retrieve(question):
        call_counter["count"] += 1
        return original_retrieve(question)

    monkeypatch.setattr(service, "_retrieve_facts", wrapped_retrieve)

    answer_first = service.answer("Где посмотреть расписание?")
    now["value"] += 5
    answer_second = service.answer("Где посмотреть расписание?")

    assert answer_first is not None
    assert answer_second is not None
    assert call_counter["count"] == 2


def test_local_ai_confidence_gate_skips_llm_on_low_score(tmp_path, monkeypatch):
    settings.LOCAL_LLM_ENABLED = True
    settings.LOCAL_LLM_MIN_CONFIDENCE_SCORE = 0.99
    settings.LOCAL_LLM_MIN_CONFIDENCE_SCORE_WITH_TOPIC = 0.99
    data_dir = tmp_path / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "misc.json").write_text(
        json.dumps(
            {
                "notes": [
                    {
                        "text": (
                            "Общая информация для студентов университета. "
                            * 6
                        )
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = LocalAIService(data_dirs=(data_dir,))

    def fake_llm(*args, **kwargs):
        raise AssertionError("LLM не должна вызываться при низкой уверенности retrieval")

    monkeypatch.setattr(service, "_generate_with_local_llm_sync", fake_llm)

    answer = service.answer("Информация для студентов")

    assert answer is not None
    assert "Вот что удалось найти" in answer
