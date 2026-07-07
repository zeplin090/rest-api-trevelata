from sqlalchemy.orm import Session
from .model_db import TicketTopic


def would_cause_cycle(db: Session, topic_id: int, new_parent_id: int | None) -> bool:
    if new_parent_id is None:
        return False
    if topic_id == new_parent_id:
        return True
        
    current_parent_id = new_parent_id
    while current_parent_id is not None:
        parent = db.query(TicketTopic).filter(TicketTopic.id == current_parent_id).first()
        if not parent:
            break
        if parent.parent_id == topic_id:
            return True  # Нашли петлю в дереве
        current_parent_id = parent.parent_id
        
    return False

def crate_topic(db: Session, code: str, title: str, parent_id: int = None, is_active: bool = True):
    exist = db.query(TicketTopic).filter(TicketTopic.code == code).first()
    if exist:
        return "CONFLICT"
    
    topic = TicketTopic(code=code, title=title, parent_id=parent_id, is_active=is_active)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic

def update_topic(db:Session, id:int, data:dict):
    pass

def soft_del_topic(db:Session, id:int):
    pass

def get_topic(db:Session, id:int):
    pass

def get_topics(db:Session, is_active:bool=None, page:int=1, per_page:int=20):
    pass