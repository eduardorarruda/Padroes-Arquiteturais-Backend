from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..schemas import (
    RelatorioContasResponse,
    ExtratoFinanceiroResponse,
    RelatorioCategoriasResponse,
    RelatorioCartaoResponse,
)
from ..services import RelatorioService
from ..models import Usuario
from .auth import obter_usuario_atual

# ==========================================
# CAMADA DE APRESENTAÇÃO: Relatórios
# ==========================================

router = APIRouter(prefix="/api/relatorios", tags=["Relatórios"])


@router.get(
    "/contas-a-pagar",
    response_model=List[RelatorioContasResponse],
    summary="Relatório de Contas a Pagar",
    description=(
        "Retorna todas as contas do tipo **PAGAR** com status **Pendente** ou **Atrasado** "
        "cujo vencimento esteja dentro do intervalo `data_inicio` e `data_fim`."
    ),
)
def relatorio_contas_a_pagar(
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.contas_a_pagar(db, usuario_id=usuario_atual.id, data_inicio=data_inicio, data_fim=data_fim)


@router.get(
    "/contas-a-receber",
    response_model=List[RelatorioContasResponse],
    summary="Relatório de Contas a Receber",
    description=(
        "Retorna todas as contas do tipo **RECEBER** com status **Pendente** ou **Atrasado** "
        "cujo vencimento esteja dentro do intervalo `data_inicio` e `data_fim`."
    ),
)
def relatorio_contas_a_receber(
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.contas_a_receber(db, usuario_id=usuario_atual.id, data_inicio=data_inicio, data_fim=data_fim)


@router.get(
    "/contas-pagas",
    response_model=List[RelatorioContasResponse],
    summary="Relatório de Contas Pagas",
    description=(
        "Retorna todas as contas do tipo **PAGAR** com status **Pago** "
        "cuja `data_pagamento` esteja dentro do intervalo `data_inicio` e `data_fim`."
    ),
)
def relatorio_contas_pagas(
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.contas_pagas(db, usuario_id=usuario_atual.id, data_inicio=data_inicio, data_fim=data_fim)


@router.get(
    "/contas-recebidas",
    response_model=List[RelatorioContasResponse],
    summary="Relatório de Contas Recebidas",
    description=(
        "Retorna todas as contas do tipo **RECEBER** com status **Recebido** "
        "cuja `data_pagamento` esteja dentro do intervalo `data_inicio` e `data_fim`."
    ),
)
def relatorio_contas_recebidas(
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.contas_recebidas(db, usuario_id=usuario_atual.id, data_inicio=data_inicio, data_fim=data_fim)


@router.get(
    "/extrato",
    response_model=ExtratoFinanceiroResponse,
    summary="Extrato Financeiro de uma Conta Corrente",
    description=(
        "Retorna uma lista cronológica de todas as **entradas** (contas recebidas) e **saídas** "
        "(contas pagas e transferências) de uma conta corrente específica no período informado. "
        "Também inclui o **saldo atual** da conta corrente."
    ),
    responses={
        404: {"description": "Conta corrente não encontrada ou não pertence ao usuário."}
    },
)
def relatorio_extrato(
    conta_corrente_id: int = Query(..., description="ID da conta corrente"),
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.extrato_financeiro(
        db,
        usuario_id=usuario_atual.id,
        conta_corrente_id=conta_corrente_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.get(
    "/categorias",
    response_model=List[RelatorioCategoriasResponse],
    summary="Relatório por Categoria",
    description=(
        "Agrupa e soma os valores das contas **pagas** e **recebidas** por categoria no período. "
        "Se `listar_financeiro=true`, retorna também os registros detalhados de cada categoria."
    ),
)
def relatorio_categorias(
    data_inicio: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    listar_financeiro: bool = Query(False, description="Se true, inclui a lista de contas detalhadas por categoria"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.por_categoria(
        db,
        usuario_id=usuario_atual.id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        listar_financeiro=listar_financeiro,
    )


@router.get(
    "/cartao",
    response_model=RelatorioCartaoResponse,
    summary="Relatório de Fatura do Cartão de Crédito",
    description=(
        "Retorna o **total da fatura** de um cartão de crédito para o mês e ano informados, "
        "junto com a lista completa de lançamentos que compõem essa fatura."
    ),
    responses={
        404: {"description": "Cartão não encontrado ou não pertence ao usuário."}
    },
)
def relatorio_cartao(
    cartao_id: int = Query(..., description="ID do cartão de crédito"),
    mes: int = Query(..., ge=1, le=12, description="Mês da fatura (1–12)"),
    ano: int = Query(..., ge=2000, description="Ano da fatura"),
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return RelatorioService.fatura_cartao(
        db,
        usuario_id=usuario_atual.id,
        cartao_id=cartao_id,
        mes=mes,
        ano=ano,
    )