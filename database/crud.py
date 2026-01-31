from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Homework, HomeworkFile, Moderator
from typing import List, Optional
import bcrypt

# ==================== HOMEWORK (замена твоих методов) ====================

async def add_homework(session: AsyncSession, user_id: int, subject: str, task: str, deadline: str) -> int:
    """Возвращает ID созданного задания (как твой старый cursor.lastrowid)"""
    hw = Homework(
        user_id=user_id,
        subject=subject,
        task=task,
        deadline=deadline
    )
    session.add(hw)
    await session.commit()
    await session.refresh(hw)
    return hw.id

async def get_user_homework(session: AsyncSession, user_id: int) -> List[Homework]:
    """Получить все задания пользователя (как твой старый метод)"""
    result = await session.execute(
        select(Homework)
        .where(Homework.user_id == user_id)
        .order_by(Homework.deadline.asc())
    )
    return result.scalars().all()

async def get_all_homework(session: AsyncSession) -> List[Homework]:
    """Все задания для общего показа"""
    result = await session.execute(
        select(Homework).order_by(Homework.created_at.desc())
    )
    return result.scalars().all()

async def get_homework_by_id(session: AsyncSession, homework_id: int, user_id: int = None) -> Optional[Homework]:

    if user_id is not None:
        result = await session.execute(
            select(Homework)
            .where(Homework.id == homework_id, Homework.user_id == user_id)
        )
    else:
        result = await session.execute(
            select(Homework).where(Homework.id == homework_id)
        )
    return result.scalar_one_or_none()

async def delete_homework(session: AsyncSession, homework_id: int, user_id: int) -> int:

    
    result = await session.execute(
        select(Homework).where(Homework.id == homework_id, Homework.user_id == user_id)
    )
    hw = result.scalar_one_or_none()
    
    if not hw:
        return 0
    
    file_count = len(hw.files) if hw.files else 0
    
    await session.delete(hw)
    await session.commit()
    return file_count

async def delete_old_records(session: AsyncSession, days: int = 30):
    """Удаляет старые записи (как твой метод)"""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    
    await session.execute(
        delete(Homework).where(Homework.created_at < cutoff)
    )
    await session.commit()

# ==================== FILES ====================

async def add_files_to_homework(session: AsyncSession, homework_id: int, files_data: list):
    """Добавляет файлы к заданию (твой старый метод)"""
    for file_data in files_data:
        file_obj = HomeworkFile(
            homework_id=homework_id,
            storage_id=file_data.get('storage_id'),
            file_type=file_data['type'],
            file_name=file_data['name'],
            file_size=file_data.get('size')
        )
        session.add(file_obj)
    await session.commit()

async def get_homework_files(session: AsyncSession, homework_id: int) -> List[HomeworkFile]:
    """Получить файлы задания"""
    result = await session.execute(
        select(HomeworkFile).where(HomeworkFile.homework_id == homework_id)
    )
    return result.scalars().all()

async def get_file_by_id(session: AsyncSession, file_id: int) -> Optional[HomeworkFile]:
    """Как твой старый get_file_by_id"""
    result = await session.execute(
        select(HomeworkFile).where(HomeworkFile.id == file_id)
    )
    return result.scalar_one_or_none()

# ==================== MODERATORS ====================

async def create_moderator(session: AsyncSession, creator_id: int, user_id: int, password: str) -> bool:
    """Создает модератора. False если уже существует."""
    
    existing = await session.get(Moderator, user_id)
    if existing:
        return False
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    mod = Moderator(
        user_id=user_id,
        password_hash=password_hash,
        created_by=creator_id
    )
    session.add(mod)
    await session.commit()
    return True

async def verify_moderator(session: AsyncSession, user_id: int, password: str) -> bool:
    """Проверка пароля"""
    mod = await session.get(Moderator, user_id)
    if not mod or not mod.is_active:
        return False
    
    return bcrypt.checkpw(password.encode('utf-8'), mod.password_hash.encode('utf-8'))

async def is_moderator(session: AsyncSession, user_id: int) -> bool:
    """Проверка является ли пользователь активным модератором"""
    mod = await session.get(Moderator, user_id)
    return mod is not None and mod.is_active

async def get_all_moderators(session: AsyncSession) -> List[Moderator]:
    """Все модераторы"""
    result = await session.execute(select(Moderator))
    return result.scalars().all()

async def deactivate_moderator(session: AsyncSession, user_id: int) -> bool:
    """Деактивация"""
    mod = await session.get(Moderator, user_id)
    if mod:
        mod.is_active = False
        await session.commit()
        return True
    return False