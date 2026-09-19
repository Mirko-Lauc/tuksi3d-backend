import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Detectar si hay una URL externa (Render/Neon) o usar la local de Docker por defecto
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://tuksi_user:tuksi_password@localhost:5432/tuksi3d_db"
)

# Ajuste automático de prefijo para compatibilidad con asyncpg si viene de Neon/Render
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Motor de conexión asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Creador de sesiones para interactuar con la base de datos
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Clase base de la que heredarán todos nuestros modelos/tablas
class Base(DeclarativeBase):
    pass

# Dependencia para obtener la sesión en los endpoints de FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session