import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal  # Импортируем твою фабрику сессий
from app.model_db import TicketTopic  # Импортируем модель для очистки

# Создаем глобального клиента, как у тебя и было
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Фикстура автоматически очищает таблицу после КАЖДОГО теста"""
    yield  # Здесь запускается сам тест
    
    # А этот код выполняется строго ПОСЛЕ теста
    db = SessionLocal()
    try:
        db.query(TicketTopic).delete()
        db.commit()
    finally:
        db.close()

# 1. ТЕСТЫ НА СОЗДАНИЕ (POST)

def test_create_topic_success():
    """Позитивный тест: успешное создание темы"""
    response = client.post(
        "/topics",
        json={"code": "visa_test", "title": "Визовые вопросы", "parent_id": None}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "visa_test"
    assert "id" in data


def test_create_topic_duplicate_code():
    """Негативный тест: попытка создать дубликат кода (409 Conflict)"""
    client.post(
        "/topics",
        json={"code": "duplicate", "title": "Оригинал"}
    )
    response = client.post(
        "/topics",
        json={"code": "duplicate", "title": "Дубликат"}
    )
    assert response.status_code == 409


def test_create_topic_missing_title():
    """Валидация: создание без обязательного поля title (400 Bad Request)"""
    response = client.post(
        "/topics",
        json={"code": "no_title"}
    )
    assert response.status_code == 400


def test_create_topic_non_existent_parent():
    """Негативный тест: указание несуществующего parent_id (400 Bad Request)"""
    response = client.post(
        "/topics",
        json={"code": "orphan_node", "title": "Сирота", "parent_id": 999999}
    )
    assert response.status_code == 400


# 2. ТЕСТЫ НА ПОЛУЧЕНИЕ (GET)

def test_get_topics_list():
    """Тест получения списка с пагинацией"""
    response = client.get("/topics?is_active=true&page=1&per_page=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_topic_not_found():
    """Тест получения несуществующей записи (404 Not Found)"""
    response = client.get("/topics/999999")
    assert response.status_code == 404


# 3. ТЕСТЫ НА ОБНОВЛЕНИЕ И ЦИКЛЫ (PUT)

def test_update_topic_success():
    """Успешное обновление заголовка"""
    create_res = client.post(
        "/topics",
        json={"code": "for_update", "title": "Старый заголовок"}
    )
    topic_id = create_res.json()["id"]

    response = client.put(
        f"/topics/{topic_id}",
        json={"title": "Новый заголовок"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Новый заголовок"


def test_update_topic_duplicate_code():
    """Негативный тест: изменение кода на уже существующий в другой записи (409 Conflict)"""
    client.post("/topics", json={"code": "code_one", "title": "Первая"})
    res_two = client.post("/topics", json={"code": "code_two", "title": "Вторая"})
    topic_id = res_two.json()["id"]

    response = client.put(f"/topics/{topic_id}", json={"code": "code_one"})
    assert response.status_code == 409


def test_update_topic_cycle():
    """Тест проверки на цикличность (400 Bad Request)"""
    res_p = client.post("/topics", json={"code": "parent_node", "title": "Родитель"})
    p_id = res_p.json()["id"]

    res_c = client.post("/topics", json={"code": "child_node", "title": "Потомок", "parent_id": p_id})
    c_id = res_c.json()["id"]

    response = client.put(
        f"/topics/{p_id}",
        json={"parent_id": c_id}
    )
    assert response.status_code == 400


def test_update_topic_non_existent_parent():
    """Негативный тест: изменение parent_id на несуществующий ID (400 Bad Request)"""
    res = client.post("/topics", json={"code": "update_parent_test", "title": "Тема"})
    topic_id = res.json()["id"]

    response = client.put(f"/topics/{topic_id}", json={"parent_id": 999999})
    assert response.status_code == 400


# 4. ТЕСТ НА МЯГКОЕ УДАЛЕНИЕ (DELETE)

def test_soft_delete_topic():
    """Тест мягкого удаления"""
    create_res = client.post("/topics", json={"code": "for_delete", "title": "На удаление"})
    topic_id = create_res.json()["id"]

    delete_res = client.delete(f"/topics/{topic_id}")
    assert delete_res.status_code == 204

    check_res = client.get(f"/topics/{topic_id}")
    if check_res.status_code == 200:
        assert check_res.json()["is_active"] is False