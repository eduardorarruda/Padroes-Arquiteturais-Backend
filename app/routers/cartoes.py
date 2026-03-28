from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas import (
    CartaoCreditoCreate, CartaoCreditoResponse,
    LancamentoCartaoCreate, LancamentoCartaoResponse,
    FechamentoFaturaRequest, ContaResponse
)
from ..services import CartaoCreditoService, LancamentoCartaoService
from ..models import Usuario
from .auth import obter_usuario_atual

# ==========================================
# CAMADA DE APRESENTAÇÃO: Cartões de Crédito
# ==========================================

router = APIRouter(prefix="/api/cartoes", tags=["Cartões de Crédito"])


# ------------------------------------------
# CRUD DE CARTÕES
# ------------------------------------------

@router.get(
    "/",
    response_model=List[CartaoCreditoResponse],
    summary="Listar cartões de crédito",
    description="Retorna uma lista com todos os cartões de crédito pertencentes ao usuário autenticado.",
    response_description="Lista de cartões de crédito encontrada."
)
def listar_cartoes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna todos os cartões de crédito do usuário autenticado."""
    return CartaoCreditoService.listar(db, usuario_id=usuario_atual.id)


@router.post(
    "/",
    response_model=CartaoCreditoResponse,
    status_code=201,
    summary="Criar cartão de crédito",
    description="Cria um novo cartão de crédito para o usuário autenticado. É necessário fornecer um `conta_corrente_id` válido e que pertença ao usuário, pois esta será a conta padrão para abatimento/baixa da fatura.",
    response_description="O cartão de crédito recém-criado.",
    responses={
        400: {"description": "Conta corrente não encontrada ou não pertence ao usuário."}
    }
)
def criar_cartao(
    dados: CartaoCreditoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Cria um novo cartão de crédito vinculado a uma conta corrente."""
    return CartaoCreditoService.criar(db, dados, usuario_id=usuario_atual.id)


# ------------------------------------------
# LANÇAMENTOS DO CARTÃO
# ------------------------------------------

@router.post(
    "/{id}/lancamentos",
    response_model=LancamentoCartaoResponse,
    status_code=201,
    summary="Criar lançamento no cartão",
    description="Registra uma nova compra, assinatura ou gasto avulso na fatura do cartão de crédito informado pelo `id`.",
    response_description="O lançamento criado com sucesso.",
    responses={
        404: {"description": "Cartão não encontrado ou não pertence ao usuário."}
    }
)
def criar_lancamento(
    id: int,
    dados: LancamentoCartaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Registra uma nova compra (lançamento) em um cartão de crédito."""
    return LancamentoCartaoService.criar(db, cartao_id=id, dados=dados, usuario_id=usuario_atual.id)


@router.get(
    "/{id}/lancamentos",
    response_model=List[LancamentoCartaoResponse],
    summary="Listar lançamentos do cartão",
    description="Lista todos os lançamentos de um determinado cartão de crédito. É possível filtrar opcionalmente por `mes_fatura` e `ano_fatura` usando query parameters.",
    response_description="Lista de lançamentos encontrada."
)
def listar_lancamentos(
    id: int,
    mes_fatura: Optional[int] = Query(None, ge=1, le=12, description="Filtrar por mês da fatura"),
    ano_fatura: Optional[int] = Query(None, ge=2000, description="Filtrar por ano da fatura"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Lista os lançamentos de um cartão, com filtro opcional por mês e ano da fatura."""
    return LancamentoCartaoService.listar(
        db, cartao_id=id, usuario_id=usuario_atual.id,
        mes_fatura=mes_fatura, ano_fatura=ano_fatura
    )


# ------------------------------------------
# FECHAMENTO DE FATURA
# ------------------------------------------

@router.post(
    "/{id}/fechar-fatura",
    response_model=ContaResponse,
    summary="Fechar fatura do cartão",
    description="Inicia a rotina de fechamento da fatura de um mês/ano específico. O sistema irá somar todos os lançamentos desse período e gerar automaticamente uma **Conta a Pagar**. A data de vencimento é calculada com base na configuração `dia_vencimento` do cartão de crédito.",
    response_description="A Conta a Pagar gerada que representa a consolidação da fatura.",
    responses={
        404: {"description": "Cartão não encontrado."},
        400: {"description": "A fatura deste mês/ano já foi fechada OU não há lançamentos para o período."}
    }
)
def fechar_fatura(
    id: int,
    dados: FechamentoFaturaRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Fecha a fatura do cartão para o mês/ano informado.
    Soma todos os lançamentos e cria uma Conta a Pagar com o valor total."""
    return CartaoCreditoService.fechar_fatura(db, cartao_id=id, dados=dados, usuario_id=usuario_atual.id)
