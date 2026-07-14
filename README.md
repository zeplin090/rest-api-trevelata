## Что реализовано

- SQLAlchemy-модель таблицы `ticket_topics`;
- подключение к PostgreSQL;
- REST API для CRUD-операций;
- проверка циклических ссылок при изменении `parent_id`;
- мягкое удаление через `is_active = False` и `deleted_at`;
- Alembic-миграции;
- тесты API в папке `tests`;
- Рабочий docker.

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

Команды кроссплатформенно (Windows PowerShell и Bash/macOS/Linux):

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Bash (Linux / macOS):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Подготовить PostgreSQL

Приложение использует переменную окружения `DATABASE_URL`. В проекте по умолчанию в исходниках локально указана строка с портом `5433`, а в `docker-compose.yml` — сервис `db` с базой `ticket_topics` на порту `5432`. Чтобы избежать путаницы, в README далее используем имя базы `ticket_topics` (синхронизировано с `docker-compose.yml`).

Пример локальной строки подключения (если вы подняли локальный Postgres на порту `5433`):

```text
postgresql://postgres:root@localhost:5433/ticket_topics
```

Создайте базу вручную при необходимости:

Windows / PowerShell:

```powershell
psql -U postgres
```

Bash:

```bash
psql -U postgres
```

SQL:

```sql
CREATE DATABASE ticket_topics;
```

### 3. Применить миграции

Локально (если у вас есть рабочая `DATABASE_URL`):

```bash
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

Первый запуск: миграции применяются автоматически — в `docker-compose.yml` команда контейнера `web` включает `alembic upgrade head` перед запуском `uvicorn`, так что при старте через Docker миграции будут накатаны автоматически.

После запуска:

- API будет доступен на `http://localhost:8000`
- Swagger UI — на `http://localhost:8000/docs`
- PostgreSQL (в контейнере) будет доступен на `localhost:5432` (сервис `db`, база `ticket_topics`)

## API

Основные эндпоинты:

- `GET /topics` — список тематик с пагинацией и фильтром `is_active`
- `GET /topics/{item_id}` — получить одну тему по `id`
- `POST /topics` — создать тему
- `PUT /topics/{item_id}` — обновить тему
- `DELETE /topics/{item_id}` — мягко удалить тему

Параметры запроса для `GET /topics`:

- `is_active` (bool, optional) — фильтр по признаку активности.
- `page` (int, optional, default=1) — номер страницы.
- `per_page` (int, optional, default=20, max=100) — элементов на страницу.

Формат ответа:

- `GET /topics` возвращает массив объектов темы:

```json
[
  {
    "id": 1,
    "code": "payment",
    "title": "Оплата и возвраты",
    "parent_id": null,
    "is_active": true,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": null,
    "deleted_at": null
  }
]
```

- `GET /topics/{item_id}` возвращает один объект темы (или `404 Not Found`).

- `POST /topics` — пример body и ответа (201 Created):

Request:

```json
{
  "code": "payment",
  "title": "Оплата и возвраты",
  "parent_id": null,
  "is_active": true
}
```

Response (201):

```json
{
  "id": 10,
  "code": "payment",
  "title": "Оплата и возвраты",
  "parent_id": null,
  "is_active": true,
  "created_at": "2026-01-01T00:00:00+00:00",
  "updated_at": null,
  "deleted_at": null
}
```

## Валидация и ошибки

- `code` должен соответствовать шаблону `^[a-zA-Z0-9_]+$`.
- При попытке создать или обновить запись с `parent_id`, указывающим на несуществующий `id`, API вернёт `400 Bad Request` с сообщением `Parent topic does not exist` (это касается и `POST /topics`, и `PUT /topics/{id}`).
- Дублирующийся `code` вернёт `409 Conflict` — это может происходить при `POST /topics` и при `PUT /topics/{id}` (при попытке сменить `code` на уже занятый).
- Попытка создать цикл через `parent_id` вернёт `400 Bad Request` с сообщением о цикличности.
- Запросы к несуществующему `id` вернут `404 Not Found`.

## Тесты

Тесты в `tests/` запускаются реальными запросами к PostgreSQL (они используют `SessionLocal` и чистят таблицу в конце каждого теста). Перед запуском `pytest` убедитесь, что база доступна:

- Поднимите БД через Docker: `docker compose up -d db` или `docker compose up --build` (миграции будут выполнены автоматически при первом старте контейнера `web`).
- Или запустите локальный Postgres на порту `5433` и создайте базу `ticket_topics` (см. выше).

Пример запуска тестов:

```bash
docker compose up -d db
pytest -q
```

Важно: теперь проект содержит `pytest.ini` и тесты запускаются из корня репозитория без дополнительных хааков или путей.

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
