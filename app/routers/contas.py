from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import ContaResponse, ContaCreate, ContaUpdate, ContaBaixa
from ..services import ContaService
from ..models import Usuario
from .auth import obter_usuario_atual

# ==========================================
# CAMADA DE APRESENTAÇÃO / CONTROLLERS
# ==========================================

router = APIRouter(prefix="/api/contas", tags=["Contas"])


# ------------------------------------------
# LISTAGENS GERAIS E POR TIPO
# ------------------------------------------

@router.get("/", response_model=List[ContaResponse], summary="Listar todas as contas")
def listar_contas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna todas as contas (a pagar e a receber) do usuário autenticado."""
    return ContaService.listar_contas(db, usuario_id=usuario_atual.id, skip=skip, limit=limit)


@router.get("/pagar", response_model=List[ContaResponse], summary="Listar contas a PAGAR")
def listar_contas_a_pagar(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna apenas as contas do tipo PAGAR do usuário autenticado."""
    return ContaService.listar_contas_a_pagar(db, usuario_id=usuario_atual.id, skip=skip, limit=limit)


@router.get("/receber", response_model=List[ContaResponse], summary="Listar contas a RECEBER")
def listar_contas_a_receber(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna apenas as contas do tipo RECEBER do usuário autenticado."""
    return ContaService.listar_contas_a_receber(db, usuario_id=usuario_atual.id, skip=skip, limit=limit)


# ------------------------------------------
# CRUD
# ------------------------------------------

@router.get("/{conta_id}", response_model=ContaResponse, summary="Obter conta por ID")
def obter_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna os detalhes de uma conta específica do usuário autenticado."""
    db_conta = ContaService.obter_conta(db, conta_id, usuario_id=usuario_atual.id)
    if not db_conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada ou não pertence ao usuário")
    return db_conta


@router.post("/", response_model=ContaResponse, status_code=201, summary="Criar conta")
def criar_conta(
    conta: ContaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Cria uma nova conta. O campo `tipo` deve ser `PAGAR` ou `RECEBER`."""
    return ContaService.criar_conta(db, conta, usuario_id=usuario_atual.id)


@router.put("/{conta_id}", response_model=ContaResponse, summary="Atualizar conta")
def atualizar_conta(
    conta_id: int,
    conta: ContaUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Atualiza os dados de uma conta existente."""
    db_conta = ContaService.atualizar_conta(db, conta_id, conta, usuario_id=usuario_atual.id)
    if not db_conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada ou não pertence ao usuário")
    return db_conta


@router.patch("/{conta_id}/baixa", response_model=ContaResponse, summary="Dar baixa em uma conta")
def baixar_conta(
    conta_id: int,
    baixa: ContaBaixa,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Realiza a baixa de uma conta, alterando o status para 'Pago' ou 'Recebido'
    e vinculando a uma conta corrente. O campo `conta_corrente_id` é obrigatório."""
    return ContaService.baixar_conta(db, conta_id, baixa, usuario_id=usuario_atual.id)


@router.delete("/{conta_id}", summary="Deletar conta")
def deletar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Remove permanentemente uma conta do usuário autenticado."""
    sucesso = ContaService.deletar_conta(db, conta_id, usuario_id=usuario_atual.id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Conta não encontrada ou não pertence ao usuário")
    return {"message": "Conta deletada com sucesso"}
