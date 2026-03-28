from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..schemas import ParceiroResponse, ParceiroCreate
from ..services import ParceiroService
from ..models import Usuario, Parceiro
from .auth import obter_usuario_atual

router = APIRouter(prefix="/api/parceiros", tags=["Parceiros"])


# Schema de atualização (campos opcionais)
class ParceiroUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None


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


# FEATURE 2 — PUT /api/parceiros/{id}
@router.put("/{id}", response_model=ParceiroResponse)
def atualizar_parceiro(
    id: int,
    dados: ParceiroUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Atualiza nome e/ou tipo de um parceiro. Filtra por id E usuario_id."""
    par = db.query(Parceiro).filter(
        Parceiro.id == id,
        Parceiro.usuario_id == usuario_atual.id,
    ).first()
    if not par:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    if dados.nome is not None:
        par.nome = dados.nome
    if dados.tipo is not None:
        if dados.tipo not in ["Cliente", "Fornecedor"]:
            raise HTTPException(status_code=400, detail="Tipo deve ser 'Cliente' ou 'Fornecedor'")
        par.tipo = dados.tipo
    db.commit()
    db.refresh(par)
    return par


# BUG 2 FIX — DELETE /api/parceiros/{id}
@router.delete("/{id}", status_code=204)
def deletar_parceiro(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Remove um parceiro. Filtra por id E usuario_id (segurança multiusuário)."""
    par = db.query(Parceiro).filter(
        Parceiro.id == id,
        Parceiro.usuario_id == usuario_atual.id,
    ).first()
    if not par:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    db.delete(par)
    db.commit()
    return None