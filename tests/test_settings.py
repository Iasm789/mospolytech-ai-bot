import importlib
import os

import pytest
from pydantic import ValidationError


def _reload_settings_module():
    os.environ.setdefault("BOT_TOKEN", "123456:abcdefghijklmnopqrstuvwxyz123456")
    import config.settings as settings_module

    return importlib.reload(settings_module)


def test_admin_ids_list_parsing():
    settings_module = _reload_settings_module()
    instance = settings_module.Settings(
        BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
        ADMIN_IDS="1, 2, x, 3",
    )
    assert instance.admin_ids_list == [1, 2, 3]


def test_invalid_log_level_raises_validation_error():
    settings_module = _reload_settings_module()
    with pytest.raises(ValidationError):
        settings_module.Settings(
            BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
            LOG_LEVEL="TRACE",
        )


def test_invalid_answer_priority_raises_validation_error():
    settings_module = _reload_settings_module()
    with pytest.raises(ValidationError):
        settings_module.Settings(
            BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
            ANSWER_PRIORITY="random_order",
        )


def test_local_llm_models_list_uses_csv_priority():
    settings_module = _reload_settings_module()
    instance = settings_module.Settings(
        BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
        LOCAL_LLM_MODEL="qwen2.5:7b",
        LOCAL_LLM_MODELS="qwen2.5:14b, qwen2.5:7b, llama3.1:8b",
    )
    assert instance.local_llm_models_list == ["qwen2.5:14b", "qwen2.5:7b", "llama3.1:8b"]


def test_local_llm_models_list_falls_back_to_single_model():
    settings_module = _reload_settings_module()
    instance = settings_module.Settings(
        BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
        LOCAL_LLM_MODEL="qwen2.5:7b",
        LOCAL_LLM_MODELS="",
    )
    assert instance.local_llm_models_list == ["qwen2.5:7b"]


def test_local_llm_routing_lists_parsing():
    settings_module = _reload_settings_module()
    instance = settings_module.Settings(
        BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
        LOCAL_LLM_SIMPLE_MODELS="qwen2.5:3b, qwen2.5:7b",
        LOCAL_LLM_COMPLEX_MODELS="qwen2.5:14b, llama3.1:8b",
    )
    assert instance.local_llm_simple_models_list == ["qwen2.5:3b", "qwen2.5:7b"]
    assert instance.local_llm_complex_models_list == ["qwen2.5:14b", "llama3.1:8b"]


def test_local_ai_context_limits_are_configurable():
    settings_module = _reload_settings_module()
    instance = settings_module.Settings(
        BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
        LOCAL_AI_RETRIEVAL_TOP_K=15,
        LOCAL_AI_LLM_MAX_CONTEXT_CHARS=5000,
    )
    assert instance.LOCAL_AI_RETRIEVAL_TOP_K == 15
    assert instance.LOCAL_AI_LLM_MAX_CONTEXT_CHARS == 5000


def test_local_llm_high_load_settings_are_configurable():
    settings_module = _reload_settings_module()
    instance = settings_module.Settings(
        BOT_TOKEN="123456:abcdefghijklmnopqrstuvwxyz123456",
        LOCAL_LLM_ADAPTIVE_LOAD_ENABLED=True,
        LOCAL_LLM_HIGH_LOAD_WAITERS_THRESHOLD=5,
        LOCAL_LLM_HIGH_LOAD_INFLIGHT_THRESHOLD=6,
        LOCAL_LLM_HIGH_LOAD_MAX_TOKENS=240,
        LOCAL_LLM_HIGH_LOAD_CONTEXT_FACTOR=0.6,
    )
    assert instance.LOCAL_LLM_HIGH_LOAD_WAITERS_THRESHOLD == 5
    assert instance.LOCAL_LLM_HIGH_LOAD_INFLIGHT_THRESHOLD == 6
    assert instance.LOCAL_LLM_HIGH_LOAD_MAX_TOKENS == 240
    assert instance.LOCAL_LLM_HIGH_LOAD_CONTEXT_FACTOR == 0.6
