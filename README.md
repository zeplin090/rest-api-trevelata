## Что реализовано

- SQLAlchemy-модель таблицы `ticket_topics`;
- подключение к PostgreSQL;
- REST API для CRUD-операций;
- проверка циклических ссылок при изменении `parent_id`;
- мягкое удаление через `is_active = False` и `deleted_at`;
- Alembic-миграции;
- тесты API в папке `tests`.

## Технологии

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- pytest

## Структура проекта

```text
.
├── app/
│   ├── crud.py                 # CRUD-логика для тематик
│   ├── database.py            # подключение к PostgreSQL и фабрика сессий
│   ├── main.py                # FastAPI endpoints
│   └── model_db.py            # SQLAlchemy-модель TicketTopic
├── migrations/
│   ├── env.py                 # настройка Alembic
│   └── versions/
│       └── ac688ad0df24_initial_commit.py
├── tests/
│   └── test_api.py            # API-тесты
├── alembic.ini                # настройки Alembic
├── docker-compose.yml         # запуск PostgreSQL + API через Docker
├── dockerfile                 # контейнер для приложения
├── requirements.txt
└── README.md
```

## Модель `ticket_topics`

Модель находится в [app/model_db.py](app/model_db.py).

Поля:

- `id` — первичный ключ;
- `code` — уникальный код тематики, строка до 64 символов;
- `title` — название тематики, строка до 200 символов;
- `parent_id` — ссылка на родительскую тематику, может быть `NULL`;
- `is_active` — флаг активности;
- `created_at` — дата создания;
- `updated_at` — дата обновления;
- `deleted_at` — дата мягкого удаления;
- `parent` / `children` — связи для работы с деревом.

## Запуск локально

### 1. Установить зависимости

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Подготовить PostgreSQL

По умолчанию приложение ожидает подключение к базе:

```text
postgresql://postgres:root@localhost:5433/ticket_db
```

Создайте базу вручную, если она ещё не существует:

```powershell
psql -U postgres
```

```sql
CREATE DATABASE ticket_db;
```

### 3. Применить миграции

```powershell
alembic upgrade head
```

### 4. Запустить API

```powershell
uvicorn app.main:app --reload
```

Swagger UI будет доступен по адресу:

```text
http://127.0.0.1:8000/docs
```

## Запуск через Docker Compose

Проект также поддерживает запуск в контейнерах:

```powershell
docker compose up --build
```

После запуска:

- API будет доступен на `http://localhost:8000`
- Swagger UI — на `http://localhost:8000/docs`
- PostgreSQL будет доступен на `localhost:5432`

> В Docker-контейнере приложение использует внутреннюю строку подключения к сервису `db` и базе `ticket_topics`.

## API

Основные эндпоинты:

- `GET /topics` — список тематик с пагинацией и фильтром `is_active`
- `GET /topics/{item_id}` — получить одну тему по `id`
- `POST /topics` — создать тему
- `PUT /topics/{item_id}` — обновить тему
- `DELETE /topics/{item_id}` — мягко удалить тему

### Пример создания темы

```http
POST /topics
Content-Type: application/json

{
  "code": "payment",
  "title": "Оплата и возвраты",
  "parent_id": null,
  "is_active": true
}
```

## Валидация и ошибки

- `code` должен соответствовать шаблону `^[a-zA-Z0-9_]+$`
- дублирующийся `code` вернёт `409 Conflict`
- попытка создать цикл через `parent_id` вернёт `400 Bad Request`
- несуществующий `id` вернёт `404 Not Found`

## Тесты

```powershell
pytest -q
```

## Полезные команды

Проверить текущие миграции:

```powershell
alembic current
```

Применить все миграции:

```powershell
alembic upgrade head
```

Откатить последнюю миграцию:

```powershell
alembic downgrade -1
```
