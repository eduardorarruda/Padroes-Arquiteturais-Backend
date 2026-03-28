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

@router.get("/", response_model=List[CartaoCreditoResponse], summary="Listar cartões de crédito")
def listar_cartoes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna todos os cartões de crédito do usuário autenticado."""
    return CartaoCreditoService.listar(db, usuario_id=usuario_atual.id)


@router.post("/", response_model=CartaoCreditoResponse, status_code=201, summary="Criar cartão de crédito")
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

@router.post("/{id}/lancamentos", response_model=LancamentoCartaoResponse, status_code=201, summary="Criar lançamento no cartão")
def criar_lancamento(
    id: int,
    dados: LancamentoCartaoCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Registra uma nova compra (lançamento) em um cartão de crédito."""
    return LancamentoCartaoService.criar(db, cartao_id=id, dados=dados, usuario_id=usuario_atual.id)


@router.get("/{id}/lancamentos", response_model=List[LancamentoCartaoResponse], summary="Listar lançamentos do cartão")
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

@router.post("/{id}/fechar-fatura", response_model=ContaResponse, summary="Fechar fatura do cartão")
def fechar_fatura(
    id: int,
    dados: FechamentoFaturaRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Fecha a fatura do cartão para o mês/ano informado.
    Soma todos os lançamentos e cria uma Conta a Pagar com o valor total."""
    return CartaoCreditoService.fechar_fatura(db, cartao_id=id, dados=dados, usuario_id=usuario_atual.id)
