from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import Conta, Usuario, Categoria, Parceiro, ContaCorrente
from .schemas import ContaCreate, ContaUpdate, UsuarioCreate, CategoriaCreate, ParceiroCreate, ContaCorrenteCreate, ContaCorrenteUpdate, ContaBaixa
from .security import obter_hash_senha

# ==========================================
# SERVIÇOS DE USUÁRIO
# ==========================================
class UsuarioService:
    @staticmethod
    def obter_usuario_por_email(db: Session, email: str):
        return db.query(Usuario).filter(Usuario.email == email).first()

    @staticmethod
    def criar_usuario(db: Session, usuario: UsuarioCreate):
        senha_hash = obter_hash_senha(usuario.senha)
        db_usuario = Usuario(
            nome=usuario.nome,
            email=usuario.email,
            senha_hash=senha_hash
        )
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario

# ==========================================
# SERVIÇOS DE CATEGORIA
# ==========================================
class CategoriaService:
    @staticmethod
    def listar_categorias(db: Session, usuario_id: int):
        return db.query(Categoria).filter(Categoria.usuario_id == usuario_id).all()

    @staticmethod
    def criar_categoria(db: Session, categoria: CategoriaCreate, usuario_id: int):
        db_categoria = Categoria(descricao=categoria.descricao, usuario_id=usuario_id)
        db.add(db_categoria)
        db.commit()
        db.refresh(db_categoria)
        return db_categoria

# ==========================================
# SERVIÇOS DE PARCEIRO
# ==========================================
class ParceiroService:
    @staticmethod
    def listar_parceiros(db: Session, usuario_id: int):
        return db.query(Parceiro).filter(Parceiro.usuario_id == usuario_id).all()

    @staticmethod
    def criar_parceiro(db: Session, parceiro: ParceiroCreate, usuario_id: int):
        db_parceiro = Parceiro(nome=parceiro.nome, tipo=parceiro.tipo, usuario_id=usuario_id)
        db.add(db_parceiro)
        db.commit()
        db.refresh(db_parceiro)
        return db_parceiro

# ==========================================
# SERVIÇOS DE CONTA CORRENTE
# ==========================================
class ContaCorrenteService:
    @staticmethod
    def listar(db: Session, usuario_id: int):
        return db.query(ContaCorrente).filter(ContaCorrente.usuario_id == usuario_id).all()

    @staticmethod
    def obter(db: Session, conta_corrente_id: int, usuario_id: int):
        return db.query(ContaCorrente).filter(
            ContaCorrente.id == conta_corrente_id,
            ContaCorrente.usuario_id == usuario_id
        ).first()

    @staticmethod
    def criar(db: Session, dados: ContaCorrenteCreate, usuario_id: int):
        db_cc = ContaCorrente(
            descricao=dados.descricao,
            saldo=dados.saldo,
            usuario_id=usuario_id
        )
        db.add(db_cc)
        db.commit()
        db.refresh(db_cc)
        return db_cc

    @staticmethod
    def atualizar(db: Session, conta_corrente_id: int, dados: ContaCorrenteUpdate, usuario_id: int):
        db_cc = db.query(ContaCorrente).filter(
            ContaCorrente.id == conta_corrente_id,
            ContaCorrente.usuario_id == usuario_id
        ).first()
        if not db_cc:
            return None

        update_data = dados.dict(exclude_unset=True) if hasattr(dados, 'dict') else dados.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_cc, key, value)

        db.commit()
        db.refresh(db_cc)
        return db_cc

    @staticmethod
    def deletar(db: Session, conta_corrente_id: int, usuario_id: int):
        db_cc = db.query(ContaCorrente).filter(
            ContaCorrente.id == conta_corrente_id,
            ContaCorrente.usuario_id == usuario_id
        ).first()
        if not db_cc:
            return None

        # Verificar se existem contas baixadas vinculadas a esta conta corrente
        contas_vinculadas = db.query(Conta).filter(
            Conta.conta_corrente_id == conta_corrente_id,
            Conta.status.in_(["Pago", "Recebido"])
        ).count()

        if contas_vinculadas > 0:
            raise HTTPException(
                status_code=400,
                detail="Não é possível excluir esta conta corrente. "
                       "Existem contas baixadas vinculadas a ela."
            )

        db.delete(db_cc)
        db.commit()
        return True

# ==========================================
# CAMADA DE SERVIÇOS / REGRAS DE NEGÓCIO DE CONTA
# ==========================================
class ContaService:
    @staticmethod
    def listar_contas(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
        return db.query(Conta).filter(Conta.usuario_id == usuario_id).offset(skip).limit(limit).all()

    @staticmethod
    def listar_contas_a_pagar(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
        return (
            db.query(Conta)
            .filter(Conta.usuario_id == usuario_id, Conta.tipo == "PAGAR")
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def listar_contas_a_receber(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
        return (
            db.query(Conta)
            .filter(Conta.usuario_id == usuario_id, Conta.tipo == "RECEBER")
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obter_conta(db: Session, conta_id: int, usuario_id: int):
        return db.query(Conta).filter(Conta.id == conta_id, Conta.usuario_id == usuario_id).first()

    @staticmethod
    def criar_conta(db: Session, conta: ContaCreate, usuario_id: int):
        conta_data = conta.dict() if hasattr(conta, 'dict') else conta.model_dump()
        db_conta = Conta(**conta_data, usuario_id=usuario_id)
        db.add(db_conta)
        db.commit()
        db.refresh(db_conta)
        return db_conta

    @staticmethod
    def atualizar_conta(db: Session, conta_id: int, conta_update: ContaUpdate, usuario_id: int):
        db_conta = db.query(Conta).filter(Conta.id == conta_id, Conta.usuario_id == usuario_id).first()
        if not db_conta:
            return None

        update_data = conta_update.dict(exclude_unset=True) if hasattr(conta_update, 'dict') else conta_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_conta, key, value)

        db.commit()
        db.refresh(db_conta)
        return db_conta

    @staticmethod
    def baixar_conta(db: Session, conta_id: int, baixa: ContaBaixa, usuario_id: int):
        """Realiza a baixa de uma conta, vinculando a uma conta corrente."""
        # Buscar a conta
        db_conta = db.query(Conta).filter(
            Conta.id == conta_id,
            Conta.usuario_id == usuario_id
        ).first()
        if not db_conta:
            raise HTTPException(status_code=404, detail="Conta não encontrada ou não pertence ao usuário")

        # Verificar se a conta já foi baixada
        if db_conta.status in ["Pago", "Recebido"]:
            raise HTTPException(status_code=400, detail="Esta conta já foi baixada")

        # Validar que a conta corrente existe e pertence ao usuário
        db_cc = db.query(ContaCorrente).filter(
            ContaCorrente.id == baixa.conta_corrente_id,
            ContaCorrente.usuario_id == usuario_id
        ).first()
        if not db_cc:
            raise HTTPException(
                status_code=400,
                detail="Conta corrente não encontrada ou não pertence ao usuário"
            )

        # Definir o status conforme o tipo da conta
        if db_conta.tipo.value == "PAGAR":
            db_conta.status = "Pago"
        else:
            db_conta.status = "Recebido"

        # Vincular a conta corrente
        db_conta.conta_corrente_id = baixa.conta_corrente_id

        db.commit()
        db.refresh(db_conta)
        return db_conta

    @staticmethod
    def deletar_conta(db: Session, conta_id: int, usuario_id: int):
        db_conta = db.query(Conta).filter(Conta.id == conta_id, Conta.usuario_id == usuario_id).first()
        if db_conta:
            db.delete(db_conta)
            db.commit()
            return True
        return False
