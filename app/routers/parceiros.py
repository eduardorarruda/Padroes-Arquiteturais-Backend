from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import ParceiroResponse, ParceiroCreate
from ..services import ParceiroService
from ..models import Usuario
from .auth import obter_usuario_atual

router = APIRouter(prefix="/api/parceiros", tags=["Parceiros"])

@router.get("/", response_model=List[ParceiroResponse])
def listar_parceiros(db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    return ParceiroService.listar_parceiros(db, usuario_id=usuario_atual.id)

@router.post("/", response_model=ParceiroResponse)
def criar_parceiro(parceiro: ParceiroCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    if parceiro.tipo not in ["Cliente", "Fornecedor"]:
        raise HTTPException(status_code=400, detail="Tipo de parceiro deve ser 'Cliente' ou 'Fornecedor'")
    return ParceiroService.criar_parceiro(db, parceiro, usuario_id=usuario_atual.id)
