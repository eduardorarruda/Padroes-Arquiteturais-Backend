from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Optional, List
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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nome": "João da Silva",
                    "email": "joao@email.com",
                    "senha": "senha_segura123"
                }
            ]
        }
    }

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
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cpf_cnpj: Optional[str] = Field(None, max_length=18, description="CPF (11 dígitos) ou CNPJ (14 dígitos), apenas números")
    endereco: Optional[str] = None
    data_nascimento_fundacao: Optional[date] = None

class ParceiroCreate(ParceiroBase):
    pass

class ParceiroUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cpf_cnpj: Optional[str] = Field(None, max_length=18)
    endereco: Optional[str] = None
    data_nascimento_fundacao: Optional[date] = None

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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Conta Itaú principal",
                    "saldo": 1500.50
                }
            ]
        }
    }

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

class TransferenciaRequest(BaseModel):
    conta_origem_id: int = Field(..., description="ID da conta corrente de origem")
    conta_destino_id: int = Field(..., description="ID da conta corrente de destino")
    valor: float = Field(..., gt=0, description="Valor da transferência")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "conta_origem_id": 1,
                    "conta_destino_id": 2,
                    "valor": 150.50
                }
            ]
        }
    }

# ==========================================
# SCHEMAS DE CARTÃO DE CRÉDITO
# ==========================================

class CartaoCreditoCreate(BaseModel):
    nome: str = Field(..., description="Nome do cartão (ex: Nubank, Visa)")
    limite: float = Field(..., gt=0, description="Limite do cartão")
    dia_fechamento: int = Field(..., ge=1, le=31, description="Dia do fechamento da fatura")
    dia_vencimento: int = Field(..., ge=1, le=31, description="Dia do vencimento da fatura")
    conta_corrente_id: int = Field(..., description="Conta corrente padrão para pagamento da fatura")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nome": "Nubank Roxinho",
                    "limite": 5000.00,
                    "dia_fechamento": 25,
                    "dia_vencimento": 5,
                    "conta_corrente_id": 1
                }
            ]
        }
    }

class CartaoCreditoUpdate(BaseModel):
    nome: Optional[str] = Field(None, description="Nome do cartão (ex: Nubank, Visa)")
    limite: Optional[float] = Field(None, gt=0, description="Limite do cartão")
    dia_fechamento: Optional[int] = Field(None, ge=1, le=31, description="Dia do fechamento da fatura")
    dia_vencimento: Optional[int] = Field(None, ge=1, le=31, description="Dia do vencimento da fatura")
    conta_corrente_id: Optional[int] = Field(None, description="Conta corrente padrão para pagamento da fatura")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "limite": 6000.00,
                    "dia_vencimento": 10
                }
            ]
        }
    }

class CartaoCreditoResponse(BaseModel):
    id: int
    nome: str
    limite: float
    limite_usado: float = Field(default=0.0, description="Limite consumido por faturas não pagas ou abertas")
    limite_livre: float = Field(default=0.0, description="Limite disponível (limite total - usado)")
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
    categoria_id: int = Field(..., description="ID da categoria da compra")
    grupo_parcelamento: Optional[str] = Field(None, description="UUID do parcelamento")
    numero_parcela: int = Field(default=1, description="Número da parcela atual")
    total_parcelas: int = Field(default=1, description="Total de parcelas")
    quantidade_parcelas: int = Field(default=1, gt=0, description="Quantidade de parcelas a gerar")
    dividir_valor: bool = Field(default=False, description="Se True, divide o valor pelas parcelas. Se False, repete.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Compra no Mercado Livre",
                    "valor": 120.50,
                    "data_compra": "2023-11-15",
                    "mes_fatura": 12,
                    "ano_fatura": 2023,
                    "categoria_id": 1,
                    "quantidade_parcelas": 3,
                    "dividir_valor": True
                }
            ]
        }
    }

class LancamentoCartaoUpdate(BaseModel):
    descricao: Optional[str] = Field(None, description="Nova descrição do lançamento")
    valor: Optional[float] = Field(None, gt=0, description="Novo valor do lançamento")
    data_compra: Optional[date] = None
    categoria_id: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Compra corrigida",
                    "valor": 99.90,
                    "categoria_id": 2
                }
            ]
        }
    }

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
    grupo_parcelamento: Optional[str] = None
    numero_parcela: int = 1
    total_parcelas: int = 1

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMA DE FECHAMENTO DE FATURA
# ==========================================

class FechamentoFaturaRequest(BaseModel):
    mes: int = Field(..., ge=1, le=12, description="Mês da fatura a fechar")
    ano: int = Field(..., ge=2000, description="Ano da fatura a fechar")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "mes": 12,
                    "ano": 2023
                }
            ]
        }
    }

# ==========================================
# SCHEMAS DE CONTA (PAGAR / RECEBER)
# ==========================================

class ContaBase(BaseModel):
    descricao: str = Field(..., description="Descrição da conta")
    valor: float = Field(..., gt=0, description="Valor monetário da conta")
    data_vencimento: date
    data_pagamento: Optional[date] = Field(None, description="Data em que a conta foi efetivamente paga/recebida")
    juros: Optional[float] = Field(default=0.0, description="Valor de juros")
    multa: Optional[float] = Field(default=0.0, description="Valor de multa")
    desconto: Optional[float] = Field(default=0.0, description="Valor de desconto")
    acrescimo: Optional[float] = Field(default=0.0, description="Valor de acréscimo")
    tipo: TipoContaEnum = Field(..., description="Tipo da conta: PAGAR ou RECEBER")
    status: str = Field(default="Pendente")
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None
    grupo_parcelamento: Optional[str] = Field(None, description="UUID agrupador de parcelas")
    numero_parcela: int = Field(default=1, description="Número da parcela atual")
    total_parcelas: int = Field(default=1, description="Total de parcelas")

class ContaCreate(ContaBase):
    conta_corrente_id: Optional[int] = Field(None, description="ID da Conta Corrente (obrigatório se status for PAGO ou RECEBIDO)")
    quantidade_parcelas: int = Field(default=1, gt=0, description="Quantidade de parcelas a gerar")
    intervalo_meses: int = Field(default=1, gt=0, description="Intervalo em meses entre cada parcela")
    dividir_valor: bool = Field(default=False, description="Se True, divide o valor total pelas parcelas. Se False, repete o valor.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Conta de Luz",
                    "valor": 180.00,
                    "data_vencimento": "2023-12-10",
                    "data_pagamento": "2023-12-10",
                    "tipo": "PAGAR",
                    "status": "PAGO",
                    "categoria_id": 2,
                    "parceiro_id": 1,
                    "conta_corrente_id": 1
                }
            ]
        }
    }

class ContaUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    tipo: Optional[TipoContaEnum] = None
    status: Optional[str] = None
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None
    conta_corrente_id: Optional[int] = None

class ContaBaixa(BaseModel):
    """Schema dedicado para a ação de baixa de uma conta."""
    conta_corrente_id: int = Field(..., description="ID da conta corrente para vincular na baixa")
    data_pagamento: Optional[date] = Field(None, description="Opcional. Se não enviado, assume a data do dia de hoje.")

class ContaResponse(ContaBase):
    id: int
    conta_corrente_id: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMAS DE NOTIFICAÇÃO
# ==========================================

class NotificacaoResponse(BaseModel):
    id: int
    mensagem: str
    lida: bool
    data_criacao: datetime
    tipo: str
    referencia_id: Optional[int] = None
    usuario_id: int

    class Config:
        orm_mode = True
        from_attributes = True

# ==========================================
# SCHEMAS DE RELATÓRIOS
# ==========================================

class RelatorioContasResponse(BaseModel):
    """Schema de resposta para os relatórios de contas a pagar, a receber, pagas e recebidas."""
    id: int
    descricao: str
    valor: float
    juros: float
    multa: float
    desconto: float
    acrescimo: float
    data_vencimento: date
    data_pagamento: Optional[date] = None
    tipo: str
    status: str
    categoria_id: Optional[int] = None
    parceiro_id: Optional[int] = None
    conta_corrente_id: Optional[int] = None
    grupo_parcelamento: Optional[str] = None
    numero_parcela: int
    total_parcelas: int

    class Config:
        orm_mode = True
        from_attributes = True


class ExtratoItemResponse(BaseModel):
    """Representa uma única linha no extrato financeiro."""
    data: date = Field(..., description="Data da movimentação (data_pagamento da conta)")
    descricao: str = Field(..., description="Descrição da movimentação")
    tipo: str = Field(..., description="'ENTRADA' ou 'SAIDA'")
    valor: float = Field(..., description="Valor da movimentação (sempre positivo)")
    origem: str = Field(..., description="'CONTA' ou 'TRANSFERENCIA'")
    referencia_id: Optional[int] = Field(None, description="ID da conta ou da transferência de origem")

    class Config:
        orm_mode = True
        from_attributes = True


class ExtratoFinanceiroResponse(BaseModel):
    """Schema de resposta do extrato financeiro de uma conta corrente."""
    conta_corrente_id: int
    descricao_conta: str = Field(..., description="Nome/descrição da conta corrente")
    saldo_atual: float = Field(..., description="Saldo atual da conta corrente no momento da consulta")
    data_inicio: date
    data_fim: date
    total_entradas: float = Field(..., description="Soma de todas as entradas no período")
    total_saidas: float = Field(..., description="Soma de todas as saídas no período")
    movimentacoes: List[ExtratoItemResponse] = Field(
        default_factory=list,
        description="Lista cronológica de todas as movimentações do período",
    )

    class Config:
        orm_mode = True
        from_attributes = True


class RelatorioCategoriasResponse(BaseModel):
    """Schema de resposta do relatório agrupado por categoria."""
    categoria_id: Optional[int] = Field(None, description="ID da categoria (None = sem categoria)")
    descricao: str = Field(..., description="Descrição da categoria")
    total_gasto: float = Field(..., description="Soma das contas do tipo PAGAR pagas no período")
    total_recebido: float = Field(..., description="Soma das contas do tipo RECEBER recebidas no período")
    contas: List[RelatorioContasResponse] = Field(
        default_factory=list,
        description="Lista de contas detalhadas (preenchida apenas quando listar_financeiro=true)",
    )

    class Config:
        orm_mode = True
        from_attributes = True


class RelatorioCartaoResponse(BaseModel):
    """Schema de resposta do relatório de fatura de cartão."""
    cartao_id: int
    nome_cartao: str
    mes: int
    ano: int
    total_fatura: float = Field(..., description="Soma de todos os lançamentos do período")
    quantidade_lancamentos: int = Field(..., description="Número de lançamentos na fatura")
    lancamentos: List[LancamentoCartaoResponse] = Field(
        default_factory=list,
        description="Lista detalhada dos lançamentos que compõem a fatura",
    )

    class Config:
        orm_mode = True
        from_attributes = True