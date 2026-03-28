from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import ContaCorrenteCreate, ContaCorrenteUpdate, ContaCorrenteResponse
from ..services import ContaCorrenteService
from ..models import Usuario
from .auth import obter_usuario_atual

# ==========================================
# CAMADA DE APRESENTAÇÃO: Contas Correntes
# ==========================================

router = APIRouter(prefix="/api/contas-correntes", tags=["Contas Correntes"])


@router.get("/", response_model=List[ContaCorrenteResponse], summary="Listar contas correntes")
def listar_contas_correntes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna todas as contas correntes do usuário autenticado."""
    return ContaCorrenteService.listar(db, usuario_id=usuario_atual.id)


@router.get("/{id}", response_model=ContaCorrenteResponse, summary="Obter conta corrente por ID")
def obter_conta_corrente(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna os detalhes de uma conta corrente específica."""
    db_cc = ContaCorrenteService.obter(db, id, usuario_id=usuario_atual.id)
    if not db_cc:
        raise HTTPException(status_code=404, detail="Conta corrente não encontrada")
    return db_cc


@router.post("/", response_model=ContaCorrenteResponse, status_code=201, summary="Criar conta corrente")
def criar_conta_corrente(
    dados: ContaCorrenteCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Cria uma nova conta corrente para o usuário autenticado."""
    return ContaCorrenteService.criar(db, dados, usuario_id=usuario_atual.id)


@router.put("/{id}", response_model=ContaCorrenteResponse, summary="Atualizar conta corrente")
def atualizar_conta_corrente(
    id: int,
    dados: ContaCorrenteUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Atualiza os dados de uma conta corrente existente."""
    db_cc = ContaCorrenteService.atualizar(db, id, dados, usuario_id=usuario_atual.id)
    if not db_cc:
        raise HTTPException(status_code=404, detail="Conta corrente não encontrada")
    return db_cc


@router.delete("/{id}", summary="Deletar conta corrente")
def deletar_conta_corrente(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Remove uma conta corrente. Falha se houver contas baixadas vinculadas."""
    resultado = ContaCorrenteService.deletar(db, id, usuario_id=usuario_atual.id)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Conta corrente não encontrada")
    # Se resultado é True, a exclusão foi bem-sucedida
    # Se houve erro (contas vinculadas), o service já lançou HTTPException 400
    return {"message": "Conta corrente deletada com sucesso"}
