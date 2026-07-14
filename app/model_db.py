from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base  # Твой базовый класс

class TicketTopic(Base):
    __tablename__ = "ticket_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_topics.id"))
    
    is_active: Mapped[bool] = mapped_column(default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    parent: Mapped[Optional["TicketTopic"]] = relationship(
        "TicketTopic", 
        remote_side=[id], 
        back_populates="children"
    )
    children: Mapped[List["TicketTopic"]] = relationship(
        "TicketTopic", 
        back_populates="parent"
    )