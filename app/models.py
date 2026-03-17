import enum
from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base

# ==========================================
# CAMADA DE DADOS: Modelos ORM (SQLAlchemy)
# ==========================================

class TipoConta(str, enum.Enum):
    PAGAR = "PAGAR"
    RECEBER = "RECEBER"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)

    contas = relationship("Conta", back_populates="dono")
    categorias = relationship("Categoria", back_populates="usuario")
    parceiros = relationship("Parceiro", back_populates="usuario")

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="categorias")
    contas = relationship("Conta", back_populates="categoria")

class Parceiro(Base):
    __tablename__ = "parceiros"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False) # Ex: "Cliente" ou "Fornecedor"
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="parceiros")
    contas = relationship("Conta", back_populates="parceiro")

class Conta(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_vencimento = Column(Date, nullable=False)
    tipo = Column(Enum(TipoConta), nullable=False)
    status = Column(String(20), nullable=False, default="Pendente")
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=True)

    dono = relationship("Usuario", back_populates="contas")
    categoria = relationship("Categoria", back_populates="contas")
    parceiro = relationship("Parceiro", back_populates="contas")
