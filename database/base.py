from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()


from config import DB_NAME
import os


current_dir = os.getcwd()
files_dir = os.path.join(current_dir, "HomeWorkBotFiles")
os.makedirs(files_dir, exist_ok=True)

db_path = os.path.join(files_dir, DB_NAME)


engine = create_async_engine(
    f"sqlite+aiosqlite:///{db_path}",
    echo=False  
)

async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Создает таблицы. Используй ТОЛЬКО для первого запуска, потом Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)