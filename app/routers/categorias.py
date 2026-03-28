from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import CategoriaResponse, CategoriaCreate
from ..services import CategoriaService
from ..models import Usuario, Categoria
from .auth import obter_usuario_atual

router = APIRouter(prefix="/api/categorias", tags=["Categorias"])


@router.get("/", response_model=List[CategoriaResponse])
def listar_categorias(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return CategoriaService.listar_categorias(db, usuario_id=usuario_atual.id)


@router.post("/", response_model=CategoriaResponse, status_code=201)
def criar_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return CategoriaService.criar_categoria(db, categoria, usuario_id=usuario_atual.id)


# FEATURE 2 — PUT /api/categorias/{id}
@router.put("/{id}", response_model=CategoriaResponse)
def atualizar_categoria(
    id: int,
    dados: CategoriaCreate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Atualiza a descrição de uma categoria. Filtra por id E usuario_id (segurança multiusuário)."""
    cat = db.query(Categoria).filter(
        Categoria.id == id,
        Categoria.usuario_id == usuario_atual.id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    cat.descricao = dados.descricao
    db.commit()
    db.refresh(cat)
    return cat


# BUG 2 FIX — DELETE /api/categorias/{id}
@router.delete("/{id}", status_code=204)
def deletar_categoria(
    id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Remove uma categoria. Filtra por id E usuario_id (segurança multiusuário)."""
    cat = db.query(Categoria).filter(
        Categoria.id == id,
        Categoria.usuario_id == usuario_atual.id,
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    db.delete(cat)
    db.commit()
    return None