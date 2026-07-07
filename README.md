# rest-api-trevelata
Сейчас в проекте реализованы:

- SQLAlchemy-модель таблицы `ticket_topics`;
- подключение к PostgreSQL;
- CRUD-функции для создания, чтения, обновления и мягкого удаления тематик;
- проверка циклов при смене `parent_id`;
- Alembic-миграция для создания таблицы;

## Стек

- Python
- PostgreSQL
- SQLAlchemy 2
- Alembic

## Структура проекта

```text
.
├── app/
│   ├── crud.py                 # CRUD-операции для ticket_topics
│   ├── database.py             # подключение к PostgreSQL и фабрика сессий
│   └── model_db.py             # SQLAlchemy-модель TicketTopic
├── migrations/
│   ├── env.py                  # настройка Alembic
│   └── versions/
│       └── ac688ad0df24_initial_commit.py
├── alembic.ini                 # настройки Alembic
├── requirements.txt
└── README.md
```

## Таблица `ticket_topics`

Модель находится в `app/model_db.py`.

Поля:

- `id` - первичный ключ, автоинкремент;
- `code` - уникальный код тематики, строка до 64 символов;
- `title` - название тематики, строка до 200 символов;
- `parent_id` - ссылка на родительскую тематику, может быть `NULL`;
- `is_active` - флаг активности;
- `created_at` - дата создания;
- `updated_at` - дата обновления;
- `deleted_at` - поле под мягкое удаление;
- `parent` / `children` - связь для работы с деревом тематик.

## Подключение к базе

Основная строка подключения находится в `app/database.py`:

```python
DATABASE_URL = "postgresql://postgres:root@localhost:5433/ticket_db"
```

В `alembic.ini` используется та же база:

```ini
sqlalchemy.url = postgresql://postgres:root@127.0.0.1:5433/ticket_db
```

Если PostgreSQL работает на другом порту или с другим паролем, поменять строку подключения в двух местах:

- `app/database.py`;
- `alembic.ini`.

## Подготовка базы данных


```powershell
psql -U postgres
```

```sql
CREATE DATABASE ticket_db;
```

Если таблица уже создана вручную, миграции можно не запускать.

Если нужно создать таблицу через Alembic:

```powershell
alembic upgrade head
```

Миграция создаёт таблицу `ticket_topics` и уникальный индекс по полю `code`.

## CRUD-функции

Функции находятся в `app/crud.py`.

### `create_topic`

Создаёт новую тематику.

```python
create_topic(
    db=db,
    code="payment",
    title="Оплата и возвраты",
    parent_id=None,
    is_active=True,
)
```

Если тема с таким `code` уже есть, функция возвращает строку:

```text
CONFLICT
```

### `get_topic`

Получает одну тематику по `id`.

```python
get_topic(db=db, id=2)
```

Если запись не найдена, возвращает:

```text
Not Found
```

### `get_topics`

Получает список тематик с пагинацией и опциональным фильтром активности.

```python
get_topics(db=db, is_active=True, page=1, per_page=20)
```

### `update_topic`

Обновляет поля тематики.

```python
update_topic(
    db=db,
    id=4,
    data={"title": "Оплата прошла"},
)
```

При обновлении `parent_id` выполняется проверка на цикл в дереве. Если новый родитель создаёт цикл, функция возвращает:

```text
CYCLE_DETECTED
```

### `soft_del_topic`

Выполняет мягкое удаление через `is_active = False`.

```python
soft_del_topic(db=db, id=4)
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
