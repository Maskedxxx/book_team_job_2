#!/usr/bin/env python3
"""
Скрипт для изучения структуры know_map_full.json 
и поиска где хранятся summary страниц.
"""

import json
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.append(str(Path(__file__).parent))

from src.book_parser.config import settings as book_settings

def analyze_know_map_structure():
    """Анализирует структуру know_map_full.json."""
    print("🔍 АНАЛИЗ СТРУКТУРЫ KNOW_MAP_FULL.JSON")
    print("="*60)
    
    know_map_path = Path(book_settings.know_map_path)
    
    with open(know_map_path, 'r', encoding='utf-8') as f:
        know_map_data = json.load(f)
    
    print("📂 ОСНОВНАЯ СТРУКТУРА:")
    print(f"  Ключи верхнего уровня: {list(know_map_data.keys())}")
    
    # Идем вглубь структуры
    content = know_map_data.get("content", {})
    print(f"  Ключи в 'content': {list(content.keys())}")
    
    parts = content.get("parts", [])
    print(f"  Количество частей: {len(parts)}")
    
    if parts:
        first_part = parts[0]
        print(f"  Ключи в первой части: {list(first_part.keys())}")
        
        chapters = first_part.get("chapters", [])
        if chapters:
            first_chapter = chapters[0]
            print(f"  Ключи в первой главе: {list(first_chapter.keys())}")
            
            subchapters = first_chapter.get("subchapters", [])
            if subchapters:
                first_subchapter = subchapters[0]
                print(f"  Ключи в первой подглаве: {list(first_subchapter.keys())}")

def find_summary_in_know_map():
    """Ищет где в know_map хранятся summary страниц."""
    print("\n🔍 ПОИСК SUMMARY В KNOW_MAP")
    print("="*50)
    
    know_map_path = Path(book_settings.know_map_path)
    
    with open(know_map_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ищем подглаву 2.4.12 для тестирования
    test_subchapter = "2.4.12"
    
    def search_recursive(obj, path=""):
        """Рекурсивно ищет объекты содержащие информацию о страницах."""
        if isinstance(obj, dict):
            # Проверяем есть ли это подглава которую мы ищем
            if obj.get("subchapter_number") == test_subchapter:
                print(f"\n✅ НАЙДЕНА ПОДГЛАВА {test_subchapter} по пути: {path}")
                print(f"  Ключи в подглаве: {list(obj.keys())}")
                
                # Проверяем есть ли информация о страницах
                pages = obj.get("pages", [])
                print(f"  Страницы: {pages}")
                
                # Ищем другие поля которые могут содержать summary
                for key, value in obj.items():
                    if "summary" in key.lower() or "content" in key.lower():
                        print(f"  Поле '{key}': {str(value)[:100]}...")
                
                # Если есть поле pages_content или что-то похожее
                if "pages_content" in obj:
                    pages_content = obj["pages_content"]
                    print(f"  📄 pages_content тип: {type(pages_content)}")
                    if isinstance(pages_content, dict):
                        print(f"  📄 pages_content ключи: {list(pages_content.keys())}")
                        
                        # Проверим содержимое для страниц 47, 48
                        for page_num in [47, 48]:
                            page_key = str(page_num)
                            if page_key in pages_content:
                                page_data = pages_content[page_key]
                                print(f"    Страница {page_num}: {list(page_data.keys()) if isinstance(page_data, dict) else type(page_data)}")
                                if isinstance(page_data, dict) and "summary" in page_data:
                                    summary = page_data["summary"]
                                    print(f"      summary: '{summary[:100]}...'")
                
                return True
            
            # Продолжаем поиск в дочерних объектах
            for key, value in obj.items():
                if search_recursive(value, f"{path}.{key}" if path else key):
                    return True
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if search_recursive(item, f"{path}[{i}]"):
                    return True
        
        return False
    
    found = search_recursive(data)
    if not found:
        print(f"❌ Подглава {test_subchapter} не найдена в know_map")

def check_all_subchapters_structure():
    """Проверяет структуру всех подглав чтобы понять паттерн хранения summary."""
    print("\n🔍 СТРУКТУРА ВСЕХ ПОДГЛАВ")
    print("="*50)
    
    know_map_path = Path(book_settings.know_map_path)
    
    with open(know_map_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    subchapters_found = []
    
    def find_subchapters(obj):
        """Находит все подглавы и их структуру."""
        if isinstance(obj, dict):
            if "subchapter_number" in obj:
                subchapter_num = obj["subchapter_number"]
                subchapters_found.append({
                    "number": subchapter_num,
                    "keys": list(obj.keys()),
                    "has_pages": "pages" in obj,
                    "has_pages_content": "pages_content" in obj,
                    "pages": obj.get("pages", [])
                })
            
            for value in obj.values():
                find_subchapters(value)
                
        elif isinstance(obj, list):
            for item in obj:
                find_subchapters(item)
    
    find_subchapters(data)
    
    print(f"📊 Найдено подглав: {len(subchapters_found)}")
    
    # Показываем первые 5 для анализа
    for i, subchapter in enumerate(subchapters_found[:5]):
        print(f"\n  {i+1}. Подглава {subchapter['number']}:")
        print(f"     Ключи: {subchapter['keys']}")
        print(f"     Есть pages: {subchapter['has_pages']}")
        print(f"     Есть pages_content: {subchapter['has_pages_content']}")
        if subchapter['pages']:
            print(f"     Страницы: {subchapter['pages']}")

def main():
    """Основная функция анализа."""
    try:
        analyze_know_map_structure()
        find_summary_in_know_map()
        check_all_subchapters_structure()
        
        print("\n" + "="*60)
        print("🎯 АНАЛИЗ ЗАВЕРШЕН")
        print("Теперь мы знаем где искать summary в know_map_full.json")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()