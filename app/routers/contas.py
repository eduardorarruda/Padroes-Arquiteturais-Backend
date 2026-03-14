from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import ContaResponse, ContaCreate, ContaUpdate
from ..services import ContaService
from ..models import Usuario
from .auth import obter_usuario_atual

# ==========================================
# CAMADA DE APRESENTAÇÃO / CONTROLLERS
# ==========================================

router = APIRouter(prefix="/api/contas", tags=["Contas a Pagar"])

@router.get("/", response_model=List[ContaResponse])
def listar_contas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    return ContaService.listar_contas(db, usuario_id=usuario_atual.id, skip=skip, limit=limit)

@router.post("/", response_model=ContaResponse)
def criar_conta(conta: ContaCreate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    return ContaService.criar_conta(db, conta, usuario_id=usuario_atual.id)

@router.put("/{conta_id}", response_model=ContaResponse)
def atualizar_conta(conta_id: int, conta: ContaUpdate, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    db_conta = ContaService.atualizar_conta(db, conta_id, conta, usuario_id=usuario_atual.id)
    if not db_conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada ou não pertence ao usuário")
    return db_conta

@router.delete("/{conta_id}")
def deletar_conta(conta_id: int, db: Session = Depends(get_db), usuario_atual: Usuario = Depends(obter_usuario_atual)):
    sucesso = ContaService.deletar_conta(db, conta_id, usuario_id=usuario_atual.id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Conta não encontrada ou não pertence ao usuário")
    return {"message": "Conta deletada com sucesso"}
