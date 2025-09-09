# Документация по сервисам AI KR

---

## Оглавление
* [Полезные команды](#полезные-команды)
* [Сервис: AI KR Book Team Service](#сервис-ai-kr-book-team-service)
* [Типовая последовательность действий при сбое](#типовая-последовательность-действий-при-сбое)
* [Типовые проблемы и решения](#типовые-проблемы-и-решения)

---

## Полезные команды

```bash
# Статус сервиса
systemctl status ai-kr-book-team.service

# Вывод последних записей journald
sudo journalctl -u ai-kr-book-team.service -e

# Быстрый просмотр лог-файла
tail -f /var/log/ai-kr/book-team.log

# Открыть unit-файл для правки
sudo nano /etc/systemd/system/ai-kr-book-team.service

# Управление сервисом
sudo systemctl start   ai-kr-book-team.service
sudo systemctl stop    ai-kr-book-team.service
sudo systemctl restart ai-kr-book-team.service
```

---

## Сервис: AI KR Book Team Service

* **systemd unit-файл**: `/etc/systemd/system/ai-kr-book-team.service`
* **Описание**: AI KR Book Team Service (бизнес-логика Клуба Руководителей — генерация ответов на запросы по данным KR через LLM)
* **Рабочая директория**: `/home/nemov_ma/book_team_job_2`
* **Пользователь / группа**: `nemov_ma` / `nemov_ma`
* **Conda-окружение**: `basic-rag` (путь `/opt/miniconda3/envs/basic-rag/bin/python`)
* **Файл переменных окружения**:

    ```bash
    /home/nemov_ma/book_team_job_2/.env
    ```

* **Логи**:

    ```lua
    /var/log/ai-kr/book-team.log
    ```

### Проверка статуса

```bash
systemctl status ai-kr-book-team.service
```

### Просмотр логов

```bash
# Вывод последних строк общего лога
tail -n 50 /var/log/ai-kr/book-team.log

# Вывод журнала systemd
sudo journalctl -u ai-kr-book-team.service -e
```

### Открытие и редактирование unit-файла

```bash
sudo nano /etc/systemd/system/ai-kr-book-team.service
```

### Запуск / остановка / перезапуск

```bash
sudo systemctl start   ai-kr-book-team.service
sudo systemctl stop    ai-kr-book-team.service
sudo systemctl restart ai-kr-book-team.service
```

---

## Типовая последовательность действий при сбое

1.  **Проверить статус сервиса**:

    ```bash
    systemctl status ai-kr-book-team.service
    ```

2.  **Открыть последние ошибки в логе**:

    ```bash
    tail -n 50 /var/log/ai-kr/book-team.log
    ```

3.  **Перезапустить сервис**:

    ```bash
    sudo systemctl restart ai-kr-book-team.service
    ```

4.  **Проверить занятые порты (если сервис не стартует из-за конфликта)**:

    ```bash
    sudo lsof -i :"${PORT}"
    ```

    Если найден чужой процесс:

    ```bash
    sudo kill <PID>
    ```

5.  **Проверить наличие и корректность файла `.env`**:
    * Убедиться, что все обязательные переменные заданы и без опечаток.

6.  **Проверить, что Conda-окружение доступно**:

    ```bash
    /opt/miniconda3/envs/basic-rag/bin/python --version
    ```

7.  **Повторная проверка статуса после действий**:

    ```bash
    systemctl status ai-kr-book-team.service
    ```

---

## Типовые проблемы и решения

| Симптом                                       | Возможная причина                                    | Решение                                                                                                      |
| :-------------------------------------------- | :--------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| Сервис не запускается                         | Файл `.env` отсутствует или неверен                 | Проверить `/home/nemov_ma/book_team_job_2/.env`, исправить ошибки, перезапустить сервис                     |
| Ошибка импорта при старте                     | Не установлен или повреждён пакет в env              | Активировать env и запустить `pip install -r requirements.txt`                                              |
| Конфликт порта (сервис не прослушивает порт) | Порт уже занят другим процессом                      | `sudo lsof -i :<PORT>` → `sudo kill <PID>` → `sudo systemctl restart ai-kr-book-team`                     |
| Недостаточно дескрипторов (EMFILE)            | Слишком маленький `LimitNOFILE`                     | Увеличить в unit-файле `LimitNOFILE=65536`, `daemon-reload` и перезапустить                                 |
| Сервис падает без логов                       | Не настроена запись в `StandardOutput`               | Проверить unit-файл — должны быть `append:/var/log/ai-kr/book-team.log`                                   |
| Отсутствие прав на запись в `/var/log/ai-kr/` | Неправильные владельцы/права директории              | `sudo chown nemov_ma:nemov_ma /var/log/ai-kr`                                                               |

---