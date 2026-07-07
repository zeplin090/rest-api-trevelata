from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class TicketTopic(Base):
    __tablename__ = "ticket_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    
    # Ссылка на родительскую категорию
    parent_id = Column(Integer, ForeignKey("ticket_topics.id"), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True) # Мягкое удаление

    # Отношения для удобной работы с деревом (необязательно, но полезно)
    parent = relationship("TicketTopic", remote_side=[id], backref="children")