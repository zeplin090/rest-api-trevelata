from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import (
    create_topic, 
    get_topics, 
    update_topic, 
    soft_del_topic, 
    get_topic
)

# Переименовали в /topics, как в твоем JSON ТЗ
app = FastAPI(title="Справочник тематик обращений", docs_url="/docs")


# Кастомный обработчик ошибок валидации
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors(), "message": "Ошибка валидации входных данных"}
    )


# СХЕМЫ ВАЛИДАЦИИ 
class TopicCreate(BaseModel):
    # regex гарантирует только латиницу, цифры и подчёркивание
    code: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    title: str = Field(..., max_length=200)  # В ТЗ написано: до 200 символов
    parent_id: int | None = None
    is_active: bool = True

class TopicUpdate(BaseModel):
    code: str | None = Field(None, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    title: str | None = Field(None, max_length=200)
    parent_id: int | None = None
    is_active: bool | None = None

# ЭНДПОИНТЫ API

@app.get("/topics")
def api_get_topics(
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Список с пагинацией и фильтрами"""
    return get_topics(db=db, is_active=is_active, page=page, per_page=per_page)


@app.get("/topics/{item_id}")
def api_get_single_topic(item_id: int, db: Session = Depends(get_db)):
    """Получение одной записи"""
    result = get_topic(db=db, id=item_id)
    if result == "Not Found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Topic not found"
        )
    return result


@app.post("/topics", status_code=status.HTTP_201_CREATED)
def api_create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    """Создание сущности"""
    result = create_topic(
        db=db, 
        code=payload.code, 
        title=payload.title, 
        parent_id=payload.parent_id, 
        is_active=payload.is_active
    )
    
    if result == "CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Topic with this code already exists"
        )
    if result == "NOT PARENT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Parent topic does not exist"
        )
    
    return result


@app.put("/topics/{item_id}")
def api_update_topic(item_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    """Обновление записи"""
    update_data = payload.model_dump(exclude_unset=True)
    
    result = update_topic(db=db, id=item_id, data=update_data)
    
    if result == "Not Found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Topic not found"
        )
    if result == "NOT PARENT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Parent topic does not exist"
        )
    if result == "CYCLE_DETECTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cyclic dependency detected in parent_id"
        )
    if result == "CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Topic with this code already exists"
        )
    return get_topic(db=db, id=item_id)


@app.delete("/topics/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_soft_delete(item_id: int, db: Session = Depends(get_db)):
    """Мягкое удаление (выставляет deleted_at)"""
    result = soft_del_topic(db=db, id=item_id)
    if result == "Not Found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Topic not found"
        )
    return None