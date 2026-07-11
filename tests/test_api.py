import pytest
from fastapi.testclient import TestClient

# Импортируем твой app из main.py
from app.main import app

# Создаем клиента для запросов
client = TestClient(app)

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
    assert data["title"] == "Визовые вопросы"
    assert "id" in data


def test_create_topic_duplicate_code():
    """Негативный тест: попытка создать дубликат кода (409 Conflict)"""
    # Первый запрос — создаем
    client.post(
        "/topics",
        json={"code": "duplicate", "title": "Оригинал", "parent_id": None}
    )
    # Второй запрос — с тем же кодом
    response = client.post(
        "/topics",
        json={"code": "duplicate", "title": "Дубликат", "parent_id": None}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Topic with this code already exists"


def test_create_topic_missing_title():
    """Валидация: создание без обязательного поля title (400 Bad Request)"""
    response = client.post(
        "/topics",
        json={"code": "no_title", "parent_id": None}
    )
    assert response.status_code == 400
    assert "message" in response.json()

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
    assert response.json()["detail"] == "Topic not found"

# 3. ТЕСТЫ НА ОБНОВЛЕНИЕ И ЦИКЛЫ (PUT)

def test_update_topic_success():
    """Успешное обновление заголовка"""
    # Сначала создаем тему для теста
    create_res = client.post(
        "/topics",
        json={"code": "for_update", "title": "Старый заголовок"}
    )
    topic_id = create_res.json()["id"]

    # Обновляем
    response = client.put(
        f"/topics/{topic_id}",
        json={"title": "Новый заголовок"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Новый заголовок"


def test_update_topic_cycle():
    """Тест проверки на цикличность (400 Bad Request)"""
    # Создаем родителя
    res_p = client.post("/topics", json={"code": "parent_node", "title": "Родитель"})
    p_id = res_p.json()["id"]

    # Создаем потомка и привязываем к родителю
    res_c = client.post("/topics", json={"code": "child_node", "title": "Потомок", "parent_id": p_id})
    c_id = res_c.json()["id"]

    # Пытаемся сделать родителя потомком своего же ребенка (петля!)
    response = client.put(
        f"/topics/{p_id}",
        json={"parent_id": c_id}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cyclic dependency detected in parent_id"

# 4. ТЕСТ НА МЯГКОЕ УДАЛЕНИЕ (DELETE)

def test_soft_delete_topic():
    """Тест мягкого удаления"""
    # Создаем тему
    create_res = client.post("/topics", json={"code": "for_delete", "title": "На удаление"})
    topic_id = create_res.json()["id"]

    # Удаляем
    delete_res = client.delete(f"/topics/{topic_id}")
    assert delete_res.status_code == 204

    # Проверяем, что при GET запросе она теперь выдает 404 или флаг изменился
    # (в зависимости от того, скрывает ли твой get_topic удаленные записи)
    check_res = client.get(f"/topics/{topic_id}")
    # Если твой get_topic просто возвращает dict, то проверим флаг активности:
    if check_res.status_code == 200:
        assert check_res.json()["is_active"] is False
        assert check_res.json()["deleted_at"] is not None