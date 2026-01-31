from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import List, Optional
from database.base import Base

class Homework(Base):
    __tablename__ = "homework"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    subject: Mapped[str] = mapped_column(String(255))
    task: Mapped[str] = mapped_column(Text)
    deadline: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Важно: связь с файлами. При удалении homework файлы удалятся автоматом
    files: Mapped[List["HomeworkFile"]] = relationship(
        back_populates="homework", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class HomeworkFile(Base):
    __tablename__ = "homework_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework.id", ondelete="CASCADE"))
    storage_id: Mapped[str] = mapped_column(String(255))  # ID в твоем storage_manager
    file_type: Mapped[str] = mapped_column(String(50))
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    homework: Mapped["Homework"] = relationship(back_populates="files")

class Moderator(Base):
    __tablename__ = "moderators"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)