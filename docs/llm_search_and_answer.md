# Документация по запуску и использованию LLM Search & Answer API-сервиса

## 1. Запуск сервиса

Для запуска микросервиса используйте следующую команду:

```bash
uvicorn src.llm_search_and_answer.main:app --host 0.0.0.0 --port 8100 --reload
```

### Параметры команды:
- `src.llm_search_and_answer.main:app` – путь к FastAPI приложению
- `--host 0.0.0.0` – делает сервис доступным на всех сетевых интерфейсах
- `--port 8100` – указывает порт для запуска сервиса
- `--reload` – включает автоматическую перезагрузку сервиса при изменении кода

После успешного запуска в консоли появится сообщение вида:

```
INFO:     Uvicorn running on http://0.0.0.0:8100 (Press CTRL+C to quit)
```

Сервис будет доступен по адресу `http://127.0.0.1:8100`

---

## 2. Реализованные API-методы

### **1. Полный пайплайн рассуждения**
- **Метод:** `POST`
- **URL:** `/llm/full-reasoning`
- **Описание:** Выполняет полный цикл анализа вопроса и генерации ответа

**Тело запроса (QuestionRequest):**
```json
{
    "question": "Текст вопроса пользователя"
}
```

**Пример ответа (FullReasoningResponse):**
```json
{
    "part_reasoning": {
        "initial_analysis": "Анализ вопроса...",
        "chapter_comparison": "Сравнение частей...",
        "final_answer": "Итоговое решение...",
        "selected_part": 2
    },
    "chapter_reasoning": {
        "preliminary_analysis": "Анализ глав...",
        "chapter_analysis": "Сравнение глав...",
        "final_reasoning": "Выбор главы...",
        "selected_chapter": 4
    },
    "subchapter_reasoning": {
        "preliminary_analysis": "Анализ подглав...",
        "subchapter_analysis": "Сравнение подглав...",
        "final_reasoning": "Выбор подглавы...",
        "selected_subchapter": "3.2"
    },
    "final_answer": {
        "answer": "Развернутый ответ на вопрос пользователя..."
    }
}
```

---

## 3. Использование API в других сервисах

### **Пример запроса в Python**

```python
import requests

def get_llm_answer(question: str) -> dict:
    response = requests.post(
        "http://127.0.0.1:8100/llm/full-reasoning",
        json={"question": question}
    )
    return response.json()

# Пример использования
result = get_llm_answer("Как создать свой первый веб-сайт?")
print(f"Ответ: {result['final_answer']['answer']}")
```

---

## 4. Архитектура сервиса

### Основные компоненты:
1. **models.py** - Pydantic модели для валидации данных
2. **services.py** - Логика работы с LLM и парсером
3. **routes.py** - API эндпоинты
4. **prompts.py** - Системные промпты для LLM
5. **config.py** - Конфигурация сервиса
6. **logger.py** - Настройка логирования

### Процесс обработки запроса:
1. Выбор релевантной части книги
2. Выбор подходящей главы
3. Выбор конкретной подглавы
4. Генерация финального ответа

Сервис зависит от работы следующих микросервисов:

1. **book_parser** (порт 8001):
  - Предоставляет API для получения структурированных данных из книги
  - Должен быть запущен для корректной работы поиска

2. **gigachat_init** (порт 8000):
  - Управляет токенами авторизации для GigaChat
  - Обеспечивает доступ к GigaChat API
  - Должен быть запущен для работы с LLM

Порядок запуска сервисов:
1. Запустить gigachat_init
2. Запустить book_parser
3. Запустить llm_search_and_answer

---

## 5. Тестирование сервиса

### Структура тестов
Тесты расположены в директории `tests/llm_search_and_answer/` и включают:

1. **test_api.py** - тесты API эндпоинтов:
  - test_full_reasoning_success - проверка успешного полного цикла рассуждения
  - test_full_reasoning_invalid_payload - проверка обработки некорректных данных

2. **test_config.py** - тесты конфигурации:
  - test_config_loading - проверка загрузки настроек из окружения
  - test_config_missing_fields - проверка валидации отсутствующих полей

3. **test_services.py** - тесты сервисных функций:
  - Тесты получения токена и взаимодействия с другими сервисами:
    * test_get_access_token_success
    * test_get_access_token_failure
    * test_fetch_content_parts
    * test_fetch_chapters_content
    * test_fetch_subchapters_content
    * test_fetch_subchapter_text
  
  - Тесты парсинга JSON:
    * test_robust_json_parse_success
    * test_robust_json_parse_with_errors
    * test_robust_json_parse_failure
  
  - Тесты работы с LLM:
    * test_get_book_part_reasoning
    * test_get_chapter_reasoning
    * test_get_subchapter_reasoning
    * test_get_final_answer

### Запуск тестов

```bash
# Запуск всех тестов
pytest tests/llm_search_and_answer/

# Запуск конкретного файла
pytest tests/llm_search_and_answer/test_services.py

# Запуск с подробным выводом
pytest -v tests/llm_search_and_answer/
```

## Дополнительно
- Сервис реализован на **FastAPI**
- Использует GigaChat API для генерации ответов
- Интегрируется с сервисом парсера книг
- Включает систему логирования операций

Swagger UI доступен по адресу:
```
http://127.0.0.1:8100/docs
```