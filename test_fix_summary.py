#!/usr/bin/env python3
"""
Тест для проверки исправления summary в fetch_subchapter_text.
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.append(str(Path(__file__).parent))

def test_new_fetch_subchapter_text():
    """Тестирует исправленную функцию fetch_subchapter_text."""
    print("🧪 ТЕСТ ИСПРАВЛЕННОЙ ФУНКЦИИ FETCH_SUBCHAPTER_TEXT")
    print("="*60)
    
    try:
        from src.llm_search_and_answer.services import fetch_subchapter_text
        
        # Тестируем на подглаве 2.4.12
        test_subchapter = "2.4.12"
        print(f"🔍 Тестируем подглаву: {test_subchapter}")
        
        result = fetch_subchapter_text(test_subchapter)
        
        print(f"✅ Функция выполнена успешно")
        print(f"📊 Длина результата: {len(result)} символов")
        
        # Проверяем что summary теперь есть
        if "<summary>" in result and "</summary>" in result:
            start = result.find("<summary>") + 9
            end = result.find("</summary>")
            summary_content = result[start:end].strip()
            
            if summary_content and summary_content != "" and len(summary_content) > 10:
                print(f"✅ Summary найден: {len(summary_content)} символов")
                print(f"📝 Начало summary: {summary_content[:100]}...")
            else:
                print(f"❌ Summary пустой или слишком короткий: '{summary_content}'")
        else:
            print(f"❌ Теги <summary> не найдены в результате")
        
        # Показываем весь результат для проверки
        print(f"\n📄 ПОЛНЫЙ РЕЗУЛЬТАТ:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

def test_pipeline_with_fix():
    """Тестирует весь пайплайн с исправлением."""
    print(f"\n🚀 ТЕСТ ПОЛНОГО ПАЙПЛАЙНА С ИСПРАВЛЕНИЕМ")
    print("="*60)
    
    try:
        from src.llm_search_and_answer.services import run_full_reasoning_pipeline
        
        # Тестовый вопрос
        test_question = """
        Вопрос: Почему отслеживание работает - назовите 4 урока о которых говорит автор.
        Ответ пользователя: Урок первый: не каждый реагирует на процесс обучения. 
        """
        
        print("🎯 Запускаем пайплайн...")
        result = run_full_reasoning_pipeline(test_question)
        
        # Проверяем итоговый контекст
        combined_content = result.get('combined_final_content', '')
        
        print(f"📊 Длина объединенного контекста: {len(combined_content)} символов")
        
        # Считаем количество непустых summary
        summary_count = 0
        empty_summary_count = 0
        
        # Ищем все summary блоки
        import re
        summary_matches = re.findall(r'<summary>(.*?)</summary>', combined_content, re.DOTALL)
        
        for summary in summary_matches:
            clean_summary = summary.strip()
            if clean_summary and len(clean_summary) > 10:
                summary_count += 1
            else:
                empty_summary_count += 1
        
        print(f"✅ Найдено заполненных summary: {summary_count}")
        print(f"❌ Найдено пустых summary: {empty_summary_count}")
        
        # Показываем пример заполненного summary
        if summary_matches:
            first_summary = summary_matches[0].strip()
            if first_summary:
                print(f"📝 Пример summary: {first_summary[:150]}...")
        
        if summary_count > 0:
            print("🎉 ИСПРАВЛЕНИЕ РАБОТАЕТ! Summary найдены и заполнены")
        else:
            print("❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ! Summary все еще пустые")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании пайплайна: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция тестирования."""
    try:
        test_new_fetch_subchapter_text()
        test_pipeline_with_fix()
        
        print("\n" + "="*60)
        print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()