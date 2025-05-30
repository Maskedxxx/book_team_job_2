# Управление сервисом Book Team Service

## Основные команды

### 🚀 Запуск и остановка
```bash
# Запустить сервис
sudo systemctl start book-team-service

# Остановить сервис  
sudo systemctl stop book-team-service

# Перезапустить сервис
sudo systemctl restart book-team-service

# Перезагрузить конфигурацию (без остановки)
sudo systemctl reload book-team-service
```

### 📊 Проверка статуса
```bash
# Текущий статус
sudo systemctl status book-team-service

# Краткий статус (работает/не работает)
sudo systemctl is-active book-team-service

# Включен ли автозапуск
sudo systemctl is-enabled book-team-service
```

### 📝 Логи и отладка
```bash
# Последние логи
sudo journalctl -u book-team-service

# Логи в реальном времени
sudo journalctl -u book-team-service -f

# Логи за последний час
sudo journalctl -u book-team-service --since "1 hour ago"

# Логи с определенного времени
sudo journalctl -u book-team-service --since "2024-05-30 10:00:00"
```

### ⚙️ Автозапуск
```bash
# Включить автозапуск при загрузке
sudo systemctl enable book-team-service

# Отключить автозапуск
sudo systemctl disable book-team-service
```

### 🔧 Модификация сервиса
```bash
# Редактировать service файл
sudo nano /etc/systemd/system/book-team-service.service

# После изменения - перезагрузить конфигурацию
sudo systemctl daemon-reload

# Перезапустить с новыми настройками
sudo systemctl restart book-team-service
```

## Проверка работы приложения

### Проверить порты
```bash
# Все порты приложения
ss -tlnp | grep -E "(8001|8010|8110|8200)"

# Конкретный сервис
curl http://localhost:8010/token/
curl http://localhost:8001/parser/parts
```

### Быстрая диагностика
```bash
# Статус + последние ошибки
sudo systemctl status book-team-service -l --no-pager

# Если сервис не запускается
sudo journalctl -u book-team-service --since "5 minutes ago"
```

## Частые проблемы

- **Сервис не запускается:** Проверь `.env` файл и права доступа
- **Порты заняты:** `sudo netstat -tlnp | grep :8001` 
- **Логи не пишутся:** Проверь права на папку `logs/`
- **После изменения кода:** `sudo systemctl restart book-team-service`