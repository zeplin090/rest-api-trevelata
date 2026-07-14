from sqlalchemy.orm import Session
from sqlalchemy import select
from .model_db import TicketTopic
from datetime import datetime, timezone

def would_cause_cycle(db: Session, topic_id: int, new_parent_id: int | None) -> bool:
    """Проверка ссылки на цикличность (SQLAlchemy 2.0 Style)

    Args:
        db (Session): Сессия базы данных
        topic_id (int): ID текущей темы, которую обновляем
        new_parent_id (int | None): Новый родительский ID для этой темы

    Returns:
        bool: True, если обнаружен цикл (петля), иначе False
    """
    if new_parent_id is None:
        return False
    if topic_id == new_parent_id:
        return True
        
    current_parent_id = new_parent_id
    while current_parent_id is not None:
        parent = db.scalar(select(TicketTopic).where(TicketTopic.id == current_parent_id))
        
        if not parent:
            break
            
        if parent.parent_id == topic_id:  # type: ignore
            return True
            
        current_parent_id = parent.parent_id
        
    return False


def create_topic(db: Session, code: str, title: str, parent_id: int | None = None, is_active: bool = True):
    """Создание тикета (SQLAlchemy 2.0 Style)

    Args:
        db (Session): База данных
        code (str): Код тикета
        title (str): Заголовок
        parent_id (int | None, optional): Родительский id. Defaults to None.
        is_active (bool, optional): Флаг активности. Defaults to True.

    Returns:
        TicketTopic | str: Добавленный тикет или строка статуса ошибки
    """
    exist = db.scalar(select(TicketTopic).where(TicketTopic.code == code))
    if exist:
        return "CONFLICT"
    
    if parent_id is not None:
        parent_exist = db.scalar(select(TicketTopic).where(TicketTopic.id == parent_id))
        if not parent_exist:
            return "NOT PARENT"

    topic = TicketTopic(code=code, title=title, parent_id=parent_id, is_active=is_active)
    db.add(topic) # Тут сам проверку на цикличность сделай, мне не нужна
    db.commit()
    db.refresh(topic)
    
    return topic


def update_topic(db: Session, id: int, data: dict):
    """Обновление тикета (SQLAlchemy 2.0 Style)

    Args:
        db (Session): База данных
        id (int): id тикета
        data (dict): данные для обновления

    Returns:
        TicketTopic | str: Обновленный объект или строка с ошибкой
    """

    db_data = db.scalar(select(TicketTopic).where(TicketTopic.id == id))
    if not db_data:
        return "Not Found"
    
    data_parent_id = data.get("parent_id")
    if data_parent_id is not None:
        parent_exist = db.scalar(select(TicketTopic).where(TicketTopic.id == data_parent_id))
        if not parent_exist:
            return "NOT PARENT"
    
    data_code = data.get("code")
    if data_code is not None:
        code_exist = db.scalar(
            select(TicketTopic).where(
                TicketTopic.code == data_code,
                TicketTopic.id != id
            )
        )
        if code_exist:
            return "CONFLICT"
    
    if "parent_id" in data:
        if would_cause_cycle(db, id, data["parent_id"]):
            return "CYCLE_DETECTED"
    
    for key, val in data.items():
        if key == "id":
            continue
        if hasattr(db_data, key):
            setattr(db_data, key, val)
    
    db.commit()


def soft_del_topic(db:Session, id:int):
    """Мягкое удаление тикета

    Args:
        db (Session): База данных
        id (int): id тикета
    Returns:
        _type_: _description_
    """
    stmt = select(TicketTopic).where(TicketTopic.id == id)
    db_data = db.scalar(stmt)
    
    if not db_data:
        return "Not Found"
    
    db_data.is_active = False  # type: ignore
    db_data.deleted_at = datetime.now(timezone.utc) # type: ignore 
    
    # 3. Фиксируем изменения в транзакции
    db.commit()
    
    return db_data


def get_topic(db:Session, id:int):
    """Получение тикета по id

    Args:
        db (Session): База данных
        id (int): id тикета

    Returns:
        dict: Строка из бд в виде словаря
    """
    topic = db.get(TicketTopic, id)
    if not topic:
        return "Not Found"
    return dict(topic.__dict__)


def get_topics(db:Session, is_active:bool|None=None, page:int=1, per_page:int=20):
    """Получение списка тикетов по id

    Args:
        db (Session): База данных
        is_active(bool): Фильтр по активным
        page(int): Страница
        per_page(int): Количество на странице

    Returns:
        list: Список тикетов из бд
    """
    stmt = select(TicketTopic)
    
    if is_active is not None:
        stmt = stmt.where(TicketTopic.is_active == is_active)
        
    offset_value = (page - 1) * per_page
    stmt = stmt.offset(offset_value).limit(per_page)
    
    return db.execute(stmt).mappings().all()