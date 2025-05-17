import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from dotenv import load_dotenv

load_dotenv()

MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')

if not MYSQL_PASSWORD:
    raise ValueError("mysql password 환경변수를 찾을 수 없습니다.")

SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://root:123456@db:3306/rpcarticle-db-1"

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
    poolclass=30
)  

Base = declarative_base()
