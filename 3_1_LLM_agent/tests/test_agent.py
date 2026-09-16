import pytest
from llm_agent.core_v2 import LLMAgent

@pytest.mark.integration
def test_calculator_query_live():
    """Реальный запуск агента для проверки математики."""
    agent = LLMAgent(local=True, ollama_model="qwen3:4b")
    query = "Сколько будет (5 + 3) * 2? Напиши только цифру."
    response = agent.process_query(query)
    assert "16" in response


@pytest.mark.integration
def test_wikipedia_query_live():
    """Реальный запуск агента для проверки WikipediaTool на русском."""
    agent = LLMAgent(local=True, ollama_model="qwen3:4b")
    query = "Что такое нейронная сеть? Ответь кратко."
    response = agent.process_query(query)
    assert "нейрон" in response.lower() or "сеть" in response.lower()


@pytest.mark.integration
def test_wikipedia_english_live():
    """Реальный запуск агента для проверки английской Wikipedia."""
    agent = LLMAgent(local=True, ollama_model="qwen3:4b")
    query = "What is machine learning? Answer briefly."
    response = agent.process_query(query)
    assert "machine learning" in response.lower() or "обучен" in response.lower()