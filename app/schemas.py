from pydantic import BaseModel, Field, EmailStr
from datetime import date
from typing import Optional

# ==========================================
# DTOs (Data Transfer Objects): Schemas Pydantic
# ==========================================

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

class ContaBase(BaseModel):
    descricao: str = Field(..., description="Descrição da conta a pagar")
    valor: float = Field(..., gt=0, description="Valor monetário da conta")
    data_vencimento: date
    status: str = Field(default="Pendente")
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None

class ContaCreate(ContaBase):
    pass

class ContaUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    status: Optional[str] = None
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None

class ContaResponse(ContaBase):
    id: int

    class Config:
        orm_mode = True # Permite que o Pydantic converta objetos SQLAlchemy para JSON (Pydantic v1)
        from_attributes = True # Suporte para Pydantic v2
