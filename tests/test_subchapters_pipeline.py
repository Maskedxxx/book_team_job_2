#!/usr/bin/env python3
"""
Тест проверки подглав для LLM пайплайна.
Проверяет корректность конфигурации подглав и работу всего пайплайна.

Запуск: python tests/test_subchapters_pipeline.py
"""

import sys
import json
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings
from src.llm_search_and_answer.services import (
    fetch_subchapter_text, 
    run_full_reasoning_pipeline
)
from src.utils.logger import get_logger

logger = get_logger("subchapters_test")

class SubchaptersTestResult:
    """Класс для хранения результатов тестирования."""
    
    def __init__(self):
        self.success = True
        self.errors = []
        self.warnings = []
        self.subchapters_data = {}
        
    def add_error(self, message: str):
        """Добавляет ошибку и помечает тест как неуспешный."""
        self.errors.append(message)
        self.success = False
        logger.error(message)
        
    def add_warning(self, message: str):
        """Добавляет предупреждение (не влияет на успешность)."""
        self.warnings.append(message)
        logger.warning(message)
        
    def print_summary(self):
        """Выводит итоговый отчет."""
        print("\n" + "="*60)
        print("ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ПОДГЛАВ")
        print("="*60)
        
        if self.success:
            print("✅ СТАТУС: ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО")
        else:
            print("❌ СТАТУС: ОБНАРУЖЕНЫ ОШИБКИ")
            
        print(f"\nПроверено подглав: {len(settings.available_subchapters)}")
        print(f"Подглавы: {', '.join(settings.available_subchapters)}")
        
        if self.errors:
            print(f"\n❌ ОШИБКИ ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
                
        if self.warnings:
            print(f"\n⚠️ ПРЕДУПРЕЖДЕНИЯ ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
                
        print("\n" + "="*60)

def test_subchapter_availability(result: SubchaptersTestResult):
    """Тест 1: Проверяет доступность всех подглав из конфига."""
    print("\n1️⃣ Проверка доступности подглав...")
    
    for subchapter in settings.available_subchapters:
        try:
            content = fetch_subchapter_text(subchapter)
            
            if not content or len(content.strip()) < 50:
                result.add_warning(f"Подглава {subchapter} содержит мало данных ({len(content)} символов)")
            else:
                result.subchapters_data[subchapter] = len(content)
                print(f"  ✅ {subchapter}: {len(content)} символов")
                
        except Exception as e:
            result.add_error(f"Подглава {subchapter} недоступна: {str(e)}")

def test_context_size(result: SubchaptersTestResult):
    """Тест 2: Проверяет размер общего контекста."""
    print("\n2️⃣ Проверка размера контекста...")
    
    total_chars = sum(result.subchapters_data.values())
    total_kb = total_chars / 1024
    
    print(f"  📊 Общий размер контекста: {total_chars} символов ({total_kb:.1f} KB)")
    
    # Проверяем лимиты (примерные значения)
    if total_chars < 1000:
        result.add_warning("Контекст очень маленький - может быть недостаточно информации для LLM")
    elif total_chars > 50000:
        result.add_warning("Контекст очень большой - может превысить лимиты LLM модели")
    else:
        print("  ✅ Размер контекста в норме")

def test_pipeline_execution(result: SubchaptersTestResult):
    """Тест 3: Проверяет работу полного пайплайна."""
    print("\n3️⃣ Проверка работы LLM пайплайна...")
    
    # Тестовый вопрос
    test_question = """
    Вопрос: Какой главный вред гнева для руководителя по мнению автора?.
    Ответ пользователя: Главные вред гнева в том что человек теряет способность меняться!.
    """
    
    try:
        pipeline_result = run_full_reasoning_pipeline(test_question)
        
        # Проверяем наличие обязательных полей
        required_fields = ['selected_subchapters', 'combined_final_content', 'final_answer']
        for field in required_fields:
            if field not in pipeline_result:
                result.add_error(f"Отсутствует поле '{field}' в результате пайплайна")
                
        # Проверяем содержимое ответа
        final_answer = pipeline_result.get('final_answer', '')
        if not final_answer or len(final_answer) < 50:
            result.add_error("LLM вернул пустой или слишком короткий ответ")
        elif 'ИТОГОВАЯ ОЦЕНКА:' not in final_answer:
            result.add_warning("Ответ LLM не содержит ожидаемый формат с итоговой оценкой")
        else:
            print(f"  ✅ Пайплайн выполнен успешно, получен ответ {len(final_answer)} символов")
            
        # Показываем начало ответа для проверки
        print(f"  📝 Начало ответа LLM: {final_answer[:1000]}...")
        
    except Exception as e:
        result.add_error(f"Ошибка выполнения пайплайна: {str(e)}")

def test_config_validation(result: SubchaptersTestResult):
    """Тест 4: Проверяет корректность конфигурации."""
    print("\n4️⃣ Проверка конфигурации...")
    
    subchapters = settings.available_subchapters
    
    if not subchapters:
        result.add_error("Список подглав пуст в конфигурации")
        return
        
    if len(subchapters) < 2:
        result.add_warning("Слишком мало подглав - рекомендуется минимум 2-3 для хорошего контекста")
    elif len(subchapters) > 10:
        result.add_warning("Много подглав - может быть избыточно для LLM анализа")
        
    # Проверяем формат номеров подглав
    for subchapter in subchapters:
        if not isinstance(subchapter, str):
            result.add_error(f"Номер подглавы должен быть строкой: {subchapter}")
        elif not ('.' in subchapter and len(subchapter.split('.')) >= 3):
            result.add_warning(f"Возможно неверный формат номера подглавы: {subchapter}")
            
    print(f"  ✅ Конфигурация содержит {len(subchapters)} подглав")

def main():
    """Основная функция запуска всех тестов."""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ПОДГЛАВ LLM ПАЙПЛАЙНА")
    print(f"Конфигурация: {settings.available_subchapters}")
    
    result = SubchaptersTestResult()
    
    # Запускаем все тесты по порядку
    test_config_validation(result)
    test_subchapter_availability(result)
    
    # Если есть критические ошибки, останавливаемся
    if not result.success:
        print("\n⚠️ Обнаружены критические ошибки, пропускаем тесты пайплайна")
        result.print_summary()
        return
        
    test_context_size(result)
    test_pipeline_execution(result)
    
    # Выводим итоговый отчет
    result.print_summary()
    
    # Возвращаем код выхода
    sys.exit(0 if result.success else 1)

if __name__ == "__main__":
    main()