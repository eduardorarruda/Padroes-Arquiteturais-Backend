from pydantic import BaseModel, Field, EmailStr
from datetime import date
from typing import Optional
from enum import Enum

# ==========================================
# DTOs (Data Transfer Objects): Schemas Pydantic
# ==========================================

class TipoContaEnum(str, Enum):
    PAGAR = "PAGAR"
    RECEBER = "RECEBER"

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str = Field(..., min_length=6)

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        orm_mode = True
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class CategoriaBase(BaseModel):
    descricao: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    usuario_id: int

    class Config:
        orm_mode = True
        from_attributes = True

class ParceiroBase(BaseModel):
    nome: str
    tipo: str = Field(..., description="Deve ser 'Cliente' ou 'Fornecedor'")

class ParceiroCreate(ParceiroBase):
    pass

class ParceiroResponse(ParceiroBase):
    id: int
    usuario_id: int

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMAS DE CONTA CORRENTE
# ==========================================

class ContaCorrenteCreate(BaseModel):
    descricao: str = Field(..., description="Descrição da conta corrente")
    saldo: float = Field(default=0, description="Saldo inicial da conta corrente")

class ContaCorrenteUpdate(BaseModel):
    descricao: Optional[str] = None
    saldo: Optional[float] = None

class ContaCorrenteResponse(BaseModel):
    id: int
    descricao: str
    saldo: float
    usuario_id: int

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMAS DE CARTÃO DE CRÉDITO
# ==========================================

class CartaoCreditoCreate(BaseModel):
    nome: str = Field(..., description="Nome do cartão (ex: Nubank, Visa)")
    limite: float = Field(..., gt=0, description="Limite do cartão")
    dia_fechamento: int = Field(..., ge=1, le=31, description="Dia do fechamento da fatura")
    dia_vencimento: int = Field(..., ge=1, le=31, description="Dia do vencimento da fatura")
    conta_corrente_id: int = Field(..., description="Conta corrente padrão para pagamento da fatura")

class CartaoCreditoResponse(BaseModel):
    id: int
    nome: str
    limite: float
    dia_fechamento: int
    dia_vencimento: int
    usuario_id: int
    conta_corrente_id: int

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMAS DE LANÇAMENTO DE CARTÃO
# ==========================================

class LancamentoCartaoCreate(BaseModel):
    descricao: str = Field(..., description="Descrição da compra")
    valor: float = Field(..., gt=0, description="Valor da compra")
    data_compra: date
    mes_fatura: int = Field(..., ge=1, le=12, description="Mês da fatura")
    ano_fatura: int = Field(..., ge=2000, description="Ano da fatura")
    categoria_id: Optional[int] = None

class LancamentoCartaoResponse(BaseModel):
    id: int
    descricao: str
    valor: float
    data_compra: date
    mes_fatura: int
    ano_fatura: int
    cartao_id: int
    categoria_id: Optional[int] = None
    usuario_id: int

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMA DE FECHAMENTO DE FATURA
# ==========================================

class FechamentoFaturaRequest(BaseModel):
    mes: int = Field(..., ge=1, le=12, description="Mês da fatura a fechar")
    ano: int = Field(..., ge=2000, description="Ano da fatura a fechar")

# ==========================================
# SCHEMAS DE CONTA (PAGAR / RECEBER)
# ==========================================

class ContaBase(BaseModel):
    descricao: str = Field(..., description="Descrição da conta")
    valor: float = Field(..., gt=0, description="Valor monetário da conta")
    data_vencimento: date
    tipo: TipoContaEnum = Field(..., description="Tipo da conta: PAGAR ou RECEBER")
    status: str = Field(default="Pendente")
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None

class ContaCreate(ContaBase):
    pass

class ContaUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    tipo: Optional[TipoContaEnum] = None
    status: Optional[str] = None
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None
    conta_corrente_id: Optional[int] = None

class ContaBaixa(BaseModel):
    """Schema dedicado para a ação de baixa de uma conta."""
    conta_corrente_id: int = Field(..., description="ID da conta corrente para vincular na baixa")

class ContaResponse(ContaBase):
    id: int
    conta_corrente_id: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True
