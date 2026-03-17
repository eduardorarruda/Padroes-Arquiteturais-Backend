from sqlalchemy.orm import Session
from .models import Conta, Usuario, Categoria, Parceiro
from .schemas import ContaCreate, ContaUpdate, UsuarioCreate, CategoriaCreate, ParceiroCreate
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
    def deletar_conta(db: Session, conta_id: int, usuario_id: int):
        db_conta = db.query(Conta).filter(Conta.id == conta_id, Conta.usuario_id == usuario_id).first()
        if db_conta:
            db.delete(db_conta)
            db.commit()
            return True
        return False
