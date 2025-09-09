#!/usr/bin/env python3
"""
Скрипт для диагностики проблемы с отсутствующими summary страниц.
Проверяет структуру данных на каждом этапе обработки.
"""

import json
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.append(str(Path(__file__).parent))

from src.book_parser.config import settings as book_settings
from src.book_parser.parsers.page_content_parser import PageContentParser

def check_raw_data_structure():
    """Проверяет структуру исходных данных в JSON файлах."""
    print("1️⃣ ПРОВЕРКА ИСХОДНЫХ ДАННЫХ")
    print("="*50)
    
    # Проверяем know_map_full.json
    know_map_path = Path(book_settings.know_map_path)
    kniga_path = Path(book_settings.kniga_path)
    
    print(f"📁 Know map файл: {know_map_path}")
    print(f"📁 Kniga файл: {kniga_path}")
    
    if not know_map_path.exists():
        print(f"❌ Файл {know_map_path} не найден!")
        return
    
    if not kniga_path.exists():
        print(f"❌ Файл {kniga_path} не найден!")
        return
    
    # Загружаем данные
    with open(know_map_path, 'r', encoding='utf-8') as f:
        know_map_data = json.load(f)
    
    with open(kniga_path, 'r', encoding='utf-8') as f:
        kniga_data = json.load(f)
    
    # Проверяем структуру kniga данных
    print("\n📖 СТРУКТУРА KNIGA ДАННЫХ:")
    book_data = kniga_data.get("book", {})
    pages = book_data.get("pages", [])
    
    print(f"  Общее количество страниц: {len(pages)}")
    
    if pages:
        # Проверяем первую страницу
        first_page = pages[0]
        print(f"  Поля в первой странице: {list(first_page.keys())}")
        
        # Проверяем наличие summary в нескольких страницах
        pages_with_summary = 0
        pages_with_empty_summary = 0
        
        for i, page in enumerate(pages[:10]):  # Проверяем первые 10 страниц
            if 'summary' in page:
                summary = page.get('summary', '')
                if summary and summary.strip():
                    pages_with_summary += 1
                else:
                    pages_with_empty_summary += 1
        
        print(f"  Страниц с непустым summary (из первых 10): {pages_with_summary}")
        print(f"  Страниц с пустым summary (из первых 10): {pages_with_empty_summary}")
        
        # Показываем пример страницы
        if len(pages) > 0:
            example_page = pages[0]
            print(f"\n  Пример первой страницы:")
            print(f"    pageNumber: {example_page.get('pageNumber')}")
            print(f"    content длина: {len(str(example_page.get('content', '')))}")
            print(f"    summary: '{example_page.get('summary', 'НЕТ ПОЛЯ')}'")
    
    return know_map_data, kniga_data

def check_parser_processing(know_map_data, kniga_data):
    """Проверяет как парсер обрабатывает данные для конкретной подглавы."""
    print("\n2️⃣ ПРОВЕРКА РАБОТЫ ПАРСЕРА")
    print("="*50)
    
    # Берем подглаву из конфига для тестирования
    test_subchapter = "2.4.12"
    print(f"🔍 Тестируем подглаву: {test_subchapter}")
    
    parser = PageContentParser(know_map_data, kniga_data)
    
    # Шаг 1: Получаем номера страниц для подглавы
    page_numbers, subchapter_title = parser.get_pages_for_subchapter(test_subchapter)
    print(f"  📄 Найденные страницы: {page_numbers}")
    print(f"  📝 Заголовок подглавы: '{subchapter_title}'")
    
    # Шаг 2: Проверяем что происходит при извлечении данных страниц
    pages_data = kniga_data.get("book", {}).get("pages", [])
    
    print(f"\n  🔍 ДЕТАЛЬНАЯ ПРОВЕРКА СТРАНИЦ:")
    for page in pages_data:
        page_num = page.get("pageNumber")
        if page_num in page_numbers:
            content_len = len(str(page.get("content", "")))
            summary = page.get("summary", "")
            
            print(f"    Страница {page_num}:")
            print(f"      content: {content_len} символов")
            print(f"      summary: '{summary}' (длина: {len(summary)})")
            print(f"      summary есть в исходных данных: {'summary' in page}")
    
    # Шаг 3: Проверяем итоговый результат парсера
    result = parser.parse_final_content(test_subchapter)
    print(f"\n  📊 ИТОГОВЫЙ РЕЗУЛЬТАТ ПАРСЕРА:")
    print(f"    Заголовок: '{result.subchapter_title}'")
    print(f"    Количество страниц: {len(result.pages)}")
    
    for page_meta in result.pages:
        print(f"    Страница {page_meta.page_number}:")
        print(f"      content: {len(page_meta.content)} символов")
        print(f"      summary: '{page_meta.summary}' (длина: {len(page_meta.summary)})")

def check_api_response():
    """Проверяет ответ API эндпоинта."""
    print("\n3️⃣ ПРОВЕРКА API ОТВЕТА")
    print("="*50)
    
    try:
        import httpx
        from src.config import settings as port_settings
        
        test_subchapter = "2.4.12"
        url = f"http://127.0.0.1:{port_settings.book_parser_port}/parser/subchapters/{test_subchapter}/content"
        
        print(f"🌐 Запрос к API: {url}")
        
        response = httpx.get(url, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"  ✅ Статус: {response.status_code}")
        print(f"  📊 Структура ответа: {list(data.keys())}")
        
        content_data = data.get("content", {})
        pages = content_data.get("pages", [])
        
        print(f"  📄 Количество страниц в ответе: {len(pages)}")
        
        for page in pages:
            print(f"    Страница {page.get('page_number')}:")
            print(f"      summary: '{page.get('summary')}' (длина: {len(page.get('summary', ''))})")
            
    except Exception as e:
        print(f"  ❌ Ошибка при запросе к API: {e}")

def main():
    """Основная функция диагностики."""
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ С SUMMARY")
    print("="*60)
    
    try:
        # Проверяем исходные данные
        know_map_data, kniga_data = check_raw_data_structure()
        
        # Проверяем работу парсера
        check_parser_processing(know_map_data, kniga_data)
        
        # Проверяем API ответ
        check_api_response()
        
        print("\n" + "="*60)
        print("🎯 АНАЛИЗ ЗАВЕРШЕН")
        print("Проверьте вывод выше, чтобы найти где теряются summary данные")
        
    except Exception as e:
        print(f"❌ Ошибка при диагностике: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()