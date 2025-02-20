# tests/llm_search_and_answer/test_services.py

import pytest
import respx
import httpx
import json
from src.llm_search_and_answer import services
from src.llm_search_and_answer.models import BookPartReasoning

# --- Тесты для get_access_token и fetch_* функций ---

@respx.mock
def test_get_access_token_success():
    token_url = "http://127.0.0.1:8000/token/token"
    expected_token = "dummy-token"
    respx.get(token_url).respond(json={"access_token": expected_token})
    
    token = services.get_access_token()
    assert token == expected_token

@respx.mock
def test_get_access_token_failure():
    token_url = "http://127.0.0.1:8000/token/token"
    respx.get(token_url).respond(status_code=500, json={"error": "Internal Server Error"})
    
    with pytest.raises(Exception):
        services.get_access_token()

@respx.mock
def test_fetch_content_parts():
    url = "http://127.0.0.1:8001/parser/parts"
    expected_text = "parts content"
    respx.get(url).respond(text=expected_text)
    
    text = services.fetch_content_parts()
    assert text == expected_text

@respx.mock
def test_fetch_chapters_content():
    part_number = 1
    url = f"http://127.0.0.1:8001/parser/parts/{part_number}/chapters"
    expected_text = "chapters content"
    respx.get(url).respond(text=expected_text)
    
    text = services.fetch_chapters_content(part_number)
    assert text == expected_text

@respx.mock
def test_fetch_subchapters_content():
    part_number = 1
    chapter_number = 1
    url = f"http://127.0.0.1:8001/parser/parts/{part_number}/chapters/{chapter_number}/subchapters"
    expected_text = "subchapters content"
    respx.get(url).respond(text=expected_text)
    
    text = services.fetch_subchapters_content(part_number, chapter_number)
    assert text == expected_text

@respx.mock
def test_fetch_subchapter_text():
    subchapter_number = "1.1"
    url = f"http://127.0.0.1:8001/parser/subchapters/{subchapter_number}/content"
    expected_text = "subchapter content"
    respx.get(url).respond(text=expected_text)
    
    text = services.fetch_subchapter_text(subchapter_number)
    assert text == expected_text

# --- Тесты для robust_json_parse ---

def test_robust_json_parse_success():
    valid_json = '{"initial_analysis": "test", "chapter_comparison": "test", "final_answer": "test", "selected_part": 1}'
    result = services.robust_json_parse(BookPartReasoning, valid_json)
    assert result.selected_part == 1

def test_robust_json_parse_with_errors():
    # Отсутствует закрывающая фигурная скобка
    broken_json = '{"initial_analysis": "test", "chapter_comparison": "test", "final_answer": "test", "selected_part": 1'
    result = services.robust_json_parse(BookPartReasoning, broken_json)
    assert result.selected_part == 1

def test_robust_json_parse_failure():
    invalid_json = "Not a JSON string"
    with pytest.raises(Exception):
        services.robust_json_parse(BookPartReasoning, invalid_json)

# --- Фейковые реализации для LLM-рассуждений ---

def fake_parse_book_part_reasoning(*args, **kwargs):
    fake_parsed = {
        "initial_analysis": "analysis",
        "chapter_comparison": "comparison",
        "final_answer": "final answer",
        "selected_part": 1
    }
    class FakeMessage:
        def model_dump_json(self):
            import json
            return json.dumps(fake_parsed)
        content = json.dumps(fake_parsed)  # Добавляем content для create
    class FakeChoice:
        message = FakeMessage()
    class FakeResponse:
        choices = [FakeChoice()]
        # Добавляем те же атрибуты, что и у модели
        initial_analysis = fake_parsed["initial_analysis"]
        chapter_comparison = fake_parsed["chapter_comparison"]
        final_answer = fake_parsed["final_answer"] 
        selected_part = fake_parsed["selected_part"]
    return FakeResponse()

def fake_parse_chapter_reasoning(*args, **kwargs):
    fake_parsed = {
        "preliminary_analysis": "pre-analysis",
        "chapter_analysis": "chapter analysis",
        "final_reasoning": "final reasoning",
        "selected_chapter": 2
    }
    class FakeMessage:
        def model_dump_json(self):
            import json
            return json.dumps(fake_parsed)
        content = json.dumps(fake_parsed)  # Добавляем content для create
    class FakeChoice:
        message = FakeMessage()
    class FakeResponse:
        choices = [FakeChoice()]
        # Добавляем те же атрибуты, что и у модели
        preliminary_analysis = fake_parsed["preliminary_analysis"]
        chapter_analysis = fake_parsed["chapter_analysis"]
        final_reasoning = fake_parsed["final_reasoning"]
        selected_chapter = fake_parsed["selected_chapter"]
    return FakeResponse()

def fake_parse_subchapter_reasoning(*args, **kwargs):
    fake_parsed = {
        "preliminary_analysis": "sub pre-analysis",
        "subchapter_analysis": "subchapter analysis",
        "final_reasoning": "sub final reasoning",
        "selected_subchapter": "1.1.1"
    }
    class FakeMessage:
        def model_dump_json(self):
            import json
            return json.dumps(fake_parsed)
        content = json.dumps(fake_parsed)  # Добавляем content для create
    class FakeChoice:
        message = FakeMessage()
    class FakeResponse:
        choices = [FakeChoice()]
        # Добавляем те же атрибуты, что и у модели
        preliminary_analysis = fake_parsed["preliminary_analysis"]
        subchapter_analysis = fake_parsed["subchapter_analysis"]
        final_reasoning = fake_parsed["final_reasoning"]
        selected_subchapter = fake_parsed["selected_subchapter"]
    return FakeResponse()

def fake_create_final_answer(*args, **kwargs):
    class FakeMessage:
        content = "Fake final answer from LLM."
    class FakeChoice:
        message = FakeMessage()
    class FakeResponse:
        choices = [FakeChoice()]
    return FakeResponse()

# Функция для создания фейкового LLM-клиента с нужной структурой
def create_fake_llm_client():
    # Создаем fake completions для beta.chat (с методом parse)
    class FakeBetaChatCompletions:
        def parse(self, *args, **kwargs):
            raise NotImplementedError("Метод parse должен быть замокан в тесте")
    # Создаем fake completions для chat (с методом create)
    class FakeChatCompletions:
        def create(self, *args, **kwargs):
            raise NotImplementedError("Метод create должен быть замокан в тесте")
    fake_client = type("FakeClient", (), {})()
    fake_client.beta = type("FakeBeta", (), {})()
    fake_client.beta.chat = type("FakeChat", (), {})()
    fake_client.beta.chat.completions = FakeBetaChatCompletions()
    # Для прямых вызовов chat.completions.create
    class FakeChatDirect:
        pass
    fake_client.chat = FakeChatDirect()
    fake_client.chat.completions = FakeChatCompletions()
    return fake_client

# --- Тесты для функций LLM-рассуждения ---

def test_get_book_part_reasoning(monkeypatch):
    fake_client = create_fake_llm_client()
    monkeypatch.setattr(fake_client.chat.completions, "create", fake_parse_book_part_reasoning)
    result = services.get_book_part_reasoning(fake_client, "dummy prompt", "dummy content", "dummy question")
    assert result.selected_part == 1
    assert result.initial_analysis == "analysis"

def test_get_chapter_reasoning(monkeypatch):
    fake_client = create_fake_llm_client()
    monkeypatch.setattr(fake_client.chat.completions, "create", fake_parse_chapter_reasoning)
    result = services.get_chapter_reasoning(fake_client, "dummy prompt", "dummy chapters content", "dummy question")
    assert result.selected_chapter == 2
    assert result.preliminary_analysis == "pre-analysis"

def test_get_subchapter_reasoning(monkeypatch):
    fake_client = create_fake_llm_client()
    monkeypatch.setattr(fake_client.chat.completions, "create", fake_parse_subchapter_reasoning)
    result = services.get_subchapter_reasoning(fake_client, "dummy prompt", "dummy subchapters content", "dummy question")
    assert result.selected_subchapter == "1.1.1"
    assert result.subchapter_analysis == "subchapter analysis"

def test_get_final_answer(monkeypatch):
    fake_client = create_fake_llm_client()
    monkeypatch.setattr(fake_client.chat.completions, "create", fake_create_final_answer)
    result = services.get_final_answer(fake_client, "dummy prompt", "dummy final content", "dummy question")
    assert isinstance(result, str) and result.strip() != ""
