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
    contas_correntes = relationship("ContaCorrente", back_populates="usuario")
    cartoes = relationship("CartaoCredito", back_populates="usuario")
    lancamentos_cartao = relationship("LancamentoCartao", back_populates="usuario")

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="categorias")
    contas = relationship("Conta", back_populates="categoria")
    lancamentos_cartao = relationship("LancamentoCartao", back_populates="categoria")

class Parceiro(Base):
    __tablename__ = "parceiros"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False) # Ex: "Cliente" ou "Fornecedor"
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="parceiros")
    contas = relationship("Conta", back_populates="parceiro")

class ContaCorrente(Base):
    __tablename__ = "contas_correntes"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    saldo = Column(Numeric(10, 2), nullable=False, default=0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="contas_correntes")
    contas = relationship("Conta", back_populates="conta_corrente")
    cartoes = relationship("CartaoCredito", back_populates="conta_corrente")

class CartaoCredito(Base):
    __tablename__ = "cartoes_credito"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    limite = Column(Numeric(10, 2), nullable=False)
    dia_fechamento = Column(Integer, nullable=False)
    dia_vencimento = Column(Integer, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    conta_corrente_id = Column(Integer, ForeignKey("contas_correntes.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="cartoes")
    conta_corrente = relationship("ContaCorrente", back_populates="cartoes")
    lancamentos = relationship("LancamentoCartao", back_populates="cartao")

class LancamentoCartao(Base):
    __tablename__ = "lancamentos_cartao"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_compra = Column(Date, nullable=False)
    mes_fatura = Column(Integer, nullable=False)
    ano_fatura = Column(Integer, nullable=False)
    cartao_id = Column(Integer, ForeignKey("cartoes_credito.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    cartao = relationship("CartaoCredito", back_populates="lancamentos")
    categoria = relationship("Categoria", back_populates="lancamentos_cartao")
    usuario = relationship("Usuario", back_populates="lancamentos_cartao")

class Conta(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(255), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=True)
    tipo = Column(Enum(TipoConta), nullable=False)
    status = Column(String(20), nullable=False, default="Pendente")
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    parceiro_id = Column(Integer, ForeignKey("parceiros.id"), nullable=True)
    conta_corrente_id = Column(Integer, ForeignKey("contas_correntes.id"), nullable=True)

    dono = relationship("Usuario", back_populates="contas")
    categoria = relationship("Categoria", back_populates="contas")
    parceiro = relationship("Parceiro", back_populates="contas")
    conta_corrente = relationship("ContaCorrente", back_populates="contas")
