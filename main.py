import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import selectinload

# Importaciones locales
from database import engine, Base, get_db
from models.user import User
from models.material import Material
from models.print import PrintJob
from schemas.user import UserCreate, UserResponse, Token
from schemas.material import MaterialCreate, MaterialResponse
from schemas.print import PrintCreate, PrintResponse, StatsResponse

# Configuración de Seguridad y JWT
SECRET_KEY = "tu_clave_secreta_super_segura_aqui"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="Tuksi 3D Backend API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialización de Tablas al Arrancar
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Funciones Auxiliares de Autenticación
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    # BYPASS ABSOLUTO: Busca cualquier usuario. Si no hay ninguno, crea a Mirko automáticamente.
    # No te va a pedir NUNCA MÁS contraseña ni token.
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(username="Mirko", email="mirkolauc12@gmail.com", hashed_password="bypass")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user

# -------------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# -------------------------------------------------------------------

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")

    result_email = await db.execute(select(User).where(User.email == user.email))
    if result_email.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    hashed_pwd = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    # Buscar usuario en BD
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crear token
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_str = create_access_token(
        data={"sub": str(user.username)}, expires_delta=access_token_expires
    )
    
    return {"access_token": token_str, "token_type": "bearer"}

# -------------------------------------------------------------------
# RUTAS DE MATERIALES
# -------------------------------------------------------------------

@app.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    material: MaterialCreate,
    is_public: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_material = Material(
        name=material.name,
        brand=material.brand,
        type=material.type,
        color=material.color,
        cost_per_kg=material.cost_per_kg,
        is_public=is_public,
        user_id=current_user.id
    )
    db.add(new_material)
    await db.commit()
    await db.refresh(new_material)
    return new_material

@app.get("/materials", response_model=List[MaterialResponse])
async def get_materials(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Material).where(
            (Material.user_id == current_user.id) | (Material.is_public == True)
        )
    )
    return result.scalars().all()

# -------------------------------------------------------------------
# RUTAS DE IMPRESIONES
# -------------------------------------------------------------------

@app.post("/prints", response_model=PrintResponse, status_code=status.HTTP_201_CREATED)
async def create_print_job(
    print_data: PrintCreate,
    is_public: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Material).where(Material.id == print_data.material_id))
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="El material especificado no existe"
        )

    material_cost = (print_data.grams_used / 1000.0) * material.cost_per_kg
    electricity_cost = print_data.print_time_hours * 0.2 * 120
    wear_cost = print_data.print_time_hours * 50
    
    total_cost = material_cost + electricity_cost + wear_cost
    profit = print_data.sale_price - total_cost

    new_print = PrintJob(
        name=print_data.name,
        material_id=print_data.material_id,
        grams_used=print_data.grams_used,
        print_time_hours=print_data.print_time_hours,
        production_cost=round(total_cost, 2),
        sale_price=print_data.sale_price,
        profit=round(profit, 2),
        is_public=is_public,
        user_id=current_user.id
    )

    db.add(new_print)
    await db.commit()
    await db.refresh(new_print)
    
    # LA SOLUCIÓN: Asignar el material en memoria para que FastAPI no intente buscarlo de nuevo
    new_print.material = material
    
    return new_print

@app.get("/prints", response_model=List[PrintResponse])
async def get_prints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.material))
        .where(
            (PrintJob.user_id == current_user.id) | (PrintJob.is_public == True)
        )
    )
    return result.scalars().all()

# -------------------------------------------------------------------
# RUTAS DE ESTADÍSTICAS
# -------------------------------------------------------------------

@app.get("/stats", response_model=StatsResponse)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(
            func.count(PrintJob.id).label("total_prints"),
            func.coalesce(func.sum(PrintJob.sale_price), 0.0).label("total_sales"),
            func.coalesce(func.sum(PrintJob.production_cost), 0.0).label("total_costs"),
            func.coalesce(func.sum(PrintJob.profit), 0.0).label("total_profit")
        ).where(PrintJob.user_id == current_user.id)
    )
    stats = result.first()
    return {
        "total_prints": stats.total_prints,
        "total_sales": stats.total_sales,
        "total_costs": stats.total_costs,
        "total_profit": stats.total_profit
    }

    # -------------------------------------------------------------------
# EDICIÓN Y ELIMINACIÓN (CRUD EXTENDIDO)
# -------------------------------------------------------------------

@app.put("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    material_data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Material).where(
            Material.id == material_id, 
            Material.user_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Material no encontrado o no tenés permiso para editarlo"
        )

    material.name = material_data.name
    material.brand = material_data.brand
    material.type = material_data.type
    material.color = material_data.color
    material.cost_per_kg = material_data.cost_per_kg

    await db.commit()
    await db.refresh(material)
    return material

@app.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Material).where(
            Material.id == material_id, 
            Material.user_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Material no encontrado"
        )

    await db.delete(material)
    await db.commit()
    return None

@app.delete("/prints/{print_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_print_job(
    print_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(PrintJob).where(
            PrintJob.id == print_id, 
            PrintJob.user_id == current_user.id
        )
    )
    print_job = result.scalar_one_or_none()
    
    if not print_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Impresión no encontrada"
        )

    await db.delete(print_job)
    await db.commit()
    return None