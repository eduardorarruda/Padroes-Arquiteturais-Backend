from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import NotificacaoResponse
from ..services import NotificacaoService
from ..models import Usuario
from .auth import obter_usuario_atual

# ==========================================
# CAMADA DE APRESENTAÇÃO / CONTROLLERS
# ==========================================

router = APIRouter(prefix="/api/notificacoes", tags=["Notificações"])


@router.get("/", response_model=List[NotificacaoResponse], summary="Listar notificações não lidas")
def listar_nao_lidas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Retorna todas as notificações não lidas do usuário autenticado."""
    return NotificacaoService.listar_nao_lidas(db, usuario_id=usuario_atual.id)


@router.patch("/{notificacao_id}/lida", response_model=NotificacaoResponse, summary="Marcar notificação como lida")
def marcar_como_lida(
    notificacao_id: int,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Marca uma notificação específica como lida."""
    return NotificacaoService.marcar_como_lida(db, notificacao_id, usuario_id=usuario_atual.id)


@router.post("/sincronizar", response_model=List[NotificacaoResponse], summary="Sincronizar notificações")
def sincronizar_notificacoes(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    """Verifica contas vencidas e fechamento de faturas, gerando notificações automaticamente.

    **Regra 1 (Atrasos):** Contas com status 'Pendente' e data de vencimento anterior a hoje
    terão o status alterado para 'Atrasado' e uma notificação será gerada.

    **Regra 2 (Faturas):** Cartões cujo dia de fechamento já passou no mês atual
    receberão uma notificação lembrando de lançar o fechamento (sem duplicar no mesmo mês).
    """
    return NotificacaoService.sincronizar_notificacoes(db, usuario_id=usuario_atual.id)
