from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import ParceiroResponse, ParceiroCreate, ParceiroUpdate  # ParceiroUpdate vem de schemas agora
from ..services import ParceiroService
from ..models import Usuario
from .auth import obter_usuario_atual

router = APIRouter(prefix="/api/parceiros", tags=["Parceiros"])


@router.get("/", response_model=List[ParceiroResponse])
def listar_parceiros(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return ParceiroService.listar_parceiros(db, usuario_id=usuario_atual.id)


@router.post("/", response_model=ParceiroResponse, status_code=201)
def criar_parceiro(
    parceiro: ParceiroCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    if parceiro.tipo not in ["Cliente", "Fornecedor"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'Cliente' ou 'Fornecedor'")
    return ParceiroService.criar_parceiro(db, parceiro, usuario_id=usuario_atual.id)


@router.put("/{id}", response_model=ParceiroResponse)
def atualizar_parceiro(
    id: int,
    dados: ParceiroUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    if dados.tipo is not None and dados.tipo not in ["Cliente", "Fornecedor"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'Cliente' ou 'Fornecedor'")
    par = ParceiroService.atualizar_parceiro(db, id, dados, usuario_id=usuario_atual.id)
    if not par:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    return par


@router.delete("/{id}", status_code=204)
def deletar_parceiro(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    from ..models import Parceiro
    par = db.query(Parceiro).filter(
        Parceiro.id == id,
        Parceiro.usuario_id == usuario_atual.id,
    ).first()
    if not par:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    db.delete(par)
    db.commit()
    return None