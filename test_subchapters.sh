#!/bin/bash
# test_subchapters.sh - Скрипт для быстрого тестирования подглав

echo "🔧 Тестирование подглав LLM пайплайна"
echo "======================================"

# Проверяем что мы в корне проекта
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: Запустите скрипт из корневой папки проекта"
    exit 1
fi

# Проверяем что сервисы запущены
echo "🔍 Проверка работы сервисов..."

# Проверяем book_parser
if ! curl -s http://127.0.0.1:8001/parser/parts > /dev/null; then
    echo "❌ Сервис book_parser не запущен (порт 8001)"
    echo "   Запустите: python main.py"
    exit 1
fi

# Проверяем gigachat_init  
if ! curl -s http://127.0.0.1:8010/token/ > /dev/null; then
    echo "❌ Сервис gigachat_init не запущен (порт 8010)"
    echo "   Запустите: python main.py"
    exit 1
fi

echo "✅ Сервисы запущены"

# Запускаем тест
echo "🚀 Запуск тестирования..."
python tests/test_subchapters_pipeline.py

# Проверяем результат
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Все тесты прошли успешно!"
    echo "   Подглавы готовы к использованию"
else
    echo ""
    echo "💥 Обнаружены проблемы!"
    echo "   Проверьте ошибки выше и исправьте конфигурацию"
fi