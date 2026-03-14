import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# ==========================================
# CAMADA DE INFRAESTRUTURA / DADOS
# ==========================================

# Lê a URL de conexão diretamente do .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida. Verifique seu arquivo .env.")

# O SQLAlchemy exige que o driver (pymysql) seja especificado na URL
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

# Caminho para o certificado salvo na raiz do projeto
# Isso resolve a exigência de SSL do Aiven Cloud
connect_args = {
    "ssl": {
        "ca": "ca.pem"
    }
}

# Cria a engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    connect_args=connect_args 
)

# Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para os modelos do ORM
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()