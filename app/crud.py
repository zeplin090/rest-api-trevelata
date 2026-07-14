from sqlalchemy.orm import Session
from sqlalchemy import select
from .model_db import TicketTopic
from datetime import datetime, timezone

def would_cause_cycle(db: Session, topic_id: int, new_parent_id: int | None) -> bool:
    """Проверка ссылки на цикличность

    Args:
        db (Session): Бдшка
        topic_id (int): id ссылки
        new_parent_id (int | None): родительский id ссылки

    Returns:
        bool: Да или нет?
    """
    if new_parent_id is None:
        return False
    if topic_id == new_parent_id:
        return True
        
    current_parent_id = new_parent_id
    while current_parent_id is not None:
        parent = db.query(TicketTopic).filter(TicketTopic.id == current_parent_id).first()
        if not parent:
            break
        if parent.parent_id == topic_id:  # type: ignore
            return True  # Нашли петлю в дереве
        current_parent_id = parent.parent_id
        
    return False


def create_topic(db: Session, code: str, title: str, parent_id: int|None = None, is_active: bool = True):
    """Создание тикета 

    Args:
        db (Session): База данных
        code (str): Код тикета
        title (str): Заголовок
        parent_id (int | None, optional): Родительский id. Defaults to None.
        is_active (bool, optional): Флаг активности. Defaults to True.

    Returns:
        _type_: Добавленный тикет (Удалить если не нужно)
    """
    exist = db.query(TicketTopic).filter(TicketTopic.code == code).first()
    if exist:
        return "CONFLICT"
    
    if parent_id is not None:
        parent_exist = db.query(TicketTopic).filter(TicketTopic.id == parent_id).first()
        if not parent_exist:
            return "NOT PARENT"


    topic = TicketTopic(code=code, title=title, parent_id=parent_id, is_active=is_active)
    db.add(topic) 
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(db:Session, id:int, data:dict):
    """Обновление тикета

    Args:
        db (Session): База данных
        id (int): id тикета
        data (dict): данные для обновления

    Returns:
        _type_: _description_
    """
    db_data = db.query(TicketTopic).filter(TicketTopic.id == id).first()
    if not db_data:
        return "Not Found"
    
    data_parent_id = data.get("parent_id")
    if  data_parent_id is not None:
        parent_exist = db.query(TicketTopic).filter(TicketTopic.id == data_parent_id).first()
        if not parent_exist:
            return "NOT PARENT"
    
    data_code = data.get("code")
    if data_code is not None:
        code_exist = db.query(TicketTopic).filter(
            TicketTopic.code == data_code,
            TicketTopic.id != id
        ).first()
        if code_exist:
            return "CONFLICT"

    
    if "parent_id" in data:
        if would_cause_cycle(db, id, data["parent_id"]):
            return "CYCLE_DETECTED"
    for key, val in data.items():
        if key == "id":
            continue
        if hasattr(db_data, key):
            setattr(db_data, key,val)
    db.commit()
    return db_data


def soft_del_topic(db:Session, id:int):
    """Мягкое удаление тикета

    Args:
        db (Session): База данных
        id (int): id тикета
    Returns:
        _type_: _description_
    """
    db_data = db.query(TicketTopic).filter(TicketTopic.id == id).first()
    if not db_data:
        return "Not Found"
    db_data.is_active = False  # type: ignore
    db_data.deleted_at = datetime.now(timezone.utc)  # type: ignore
    db.commit()


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
    t_dict = dict(topic.__dict__)
    t_dict.pop("_sa_instance_state", None)
    return t_dict


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
    
    # Выполняем запрос. .scalars().all() вернет список объектов TicketTopic
    topics = db.execute(stmt).scalars().all()
    
    # Очищаем от _sa_instance_state
    result = []
    for topic in topics:
        t_dict = dict(topic.__dict__)
        t_dict.pop("_sa_instance_state", None)
        result.append(t_dict)
        
    return result