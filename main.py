import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
from passlib.context import CryptContext
from jose import JWTError, jwt

from database import engine, Base, get_db
from models.user import User
from models.material import Material
from models.print import PrintJob
from models.product import Product

from schemas.user import UserCreate, UserResponse, Token
from schemas.material import MaterialCreate, MaterialResponse
from schemas.print import PrintCreate, PrintResponse, StatsResponse
from schemas.product import ProductCreate, ProductResponse

# Configuración de Seguridad y JWT
SECRET_KEY = "tuksi3d_clave_secreta_super_segura_para_produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 días de duración

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="Tuksi 3D Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Funciones Auxiliares de Seguridad
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Validación de Usuario Autenticado (JWT Real)
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

# -------------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# -------------------------------------------------------------------

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")

    hashed_pwd = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# -------------------------------------------------------------------
# RUTAS DE MATERIALES (INDIVIDUALES)
# -------------------------------------------------------------------

@app.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    material: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_material = Material(
        name=material.name,
        brand=material.brand,
        type=material.type,
        color=material.color,
        cost_per_kg=material.cost_per_kg,
        stock_grams=material.stock_grams or 1000.0,
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
    result = await db.execute(select(Material).where(Material.user_id == current_user.id))
    return result.scalars().all()

# -------------------------------------------------------------------
# RUTAS DE IMPRESIONES (INDIVIDUALES)
# -------------------------------------------------------------------

@app.post("/prints", response_model=PrintResponse, status_code=status.HTTP_201_CREATED)
async def create_print_job(
    print_data: PrintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Material).where(Material.id == print_data.material_id, Material.user_id == current_user.id)
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="El material no existe o no te pertenece")

    material.stock_grams = max(0.0, material.stock_grams - print_data.grams_used)

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
        client_name=print_data.client_name,
        client_phone=print_data.client_phone,
        status=print_data.status or "Pendiente",
        user_id=current_user.id
    )

    db.add(new_print)
    await db.commit()
    await db.refresh(new_print)
    new_print.material = material
    return new_print

@app.put("/prints/{print_id}/status")
async def update_print_status(
    print_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(PrintJob).where(PrintJob.id == print_id, PrintJob.user_id == current_user.id))
    print_job = result.scalar_one_or_none()
    if not print_job:
        raise HTTPException(status_code=404, detail="Impresión no encontrada")
    
    print_job.status = new_status
    await db.commit()
    return {"message": "Estado actualizado", "status": new_status}

@app.get("/prints", response_model=List[PrintResponse])
async def get_prints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(PrintJob)
        .options(selectinload(PrintJob.material))
        .where(PrintJob.user_id == current_user.id)
    )
    return result.scalars().all()

@app.delete("/prints/{print_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_print_job(
    print_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(PrintJob).where(PrintJob.id == print_id, PrintJob.user_id == current_user.id))
    print_job = result.scalar_one_or_none()
    if print_job:
        await db.delete(print_job)
        await db.commit()
    return None

# -------------------------------------------------------------------
# RUTAS DE CATÁLOGO (COMPARTIDO ENTRE TODOS LOS USUARIOS)
# -------------------------------------------------------------------

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@app.get("/products", response_model=List[ProductResponse])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    return result.scalars().all()

# -------------------------------------------------------------------
# ESTADÍSTICAS & SERVICIO WEB
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

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    return "frontend/index.html"