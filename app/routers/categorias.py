from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import CategoriaResponse, CategoriaCreate
from ..services import CategoriaService
from ..models import Usuario
from .auth import obter_usuario_atual

router = APIRouter(prefix="/api/categorias", tags=["Categorias"])

@router.get("/", response_model=List[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    return CategoriaService.listar_categorias(db, usuario_id=usuario_atual.id)

@router.post("/", response_model=CategoriaResponse)
def criar_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    return CategoriaService.criar_categoria(db, categoria, usuario_id=usuario_atual.id)
