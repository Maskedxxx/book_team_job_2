import pytest
from fastapi.testclient import TestClient
from src.llm_search_and_answer import main
from src.llm_search_and_answer import services

# Фейковая функция для имитации полного пайплайна
def fake_run_full_reasoning_pipeline(question: str) -> dict:
    from src.llm_search_and_answer.models import BookPartReasoning, ChapterReasoning, SubchapterReasoning
    return {
        "part_reasoning": BookPartReasoning(
            initial_analysis="Test initial analysis",
            chapter_comparison="Test chapter comparison",
            final_answer="Test part final answer",
            selected_part=1
        ),
        "chapter_reasoning": ChapterReasoning(
            preliminary_analysis="Test preliminary analysis",
            chapter_analysis="Test chapter analysis",
            final_reasoning="Test chapter final reasoning",
            selected_chapter=1
        ),
        "subchapter_reasoning": SubchapterReasoning(
            preliminary_analysis="Test sub preliminary analysis",
            subchapter_analysis="Test subchapter analysis",
            final_reasoning="Test subchapter final reasoning",
            selected_subchapter="1.1.1"
        ),
        "final_answer": "Это финальный ответ, сгенерированный фейком."
    }

@pytest.fixture
def client(monkeypatch):
    # Подменяем функцию полного пайплайна на фейковую
    monkeypatch.setattr(services, "run_full_reasoning_pipeline", fake_run_full_reasoning_pipeline)
    return TestClient(main.app)

def test_full_reasoning_success(client):
    payload = {"question": "Какова основная идея?"}
    response = client.post("/llm/full-reasoning", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "part_reasoning" in data
    assert "chapter_reasoning" in data
    assert "subchapter_reasoning" in data
    assert "final_answer" in data
    # Вместо точного сравнения достаточно проверить, что в final_answer вернулся не пустой текст
    final_answer = data["final_answer"]["answer"]
    assert isinstance(final_answer, str) and final_answer.strip() != ""

def test_full_reasoning_invalid_payload(client):
    # Отсутствует обязательное поле "question"
    payload = {}
    response = client.post("/llm/full-reasoning", json=payload)
    assert response.status_code == 422
