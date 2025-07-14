import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.user_models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Configuration
DATABASE_URL = "sqlite+aiosqlite:///auth.db"
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

if not SECRET_KEY:
    logging.error("SECRET_KEY not set in .env file")
    raise ValueError("SECRET_KEY not set in .env")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Using DATABASE_URL: {DATABASE_URL}")

# Database setup
try:
    engine = create_async_engine(DATABASE_URL, echo=True)
    logger.info(f"Database engine created with dialect: {engine.dialect.name}, driver: {engine.dialect.driver}")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI setup
app = FastAPI(
    title="Authentication API",
    version="1.0.0",
    description="Handles user registration and login"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with SessionLocal() as db:
        yield db

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")