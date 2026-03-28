from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import date
from .models import Conta, Usuario, Categoria, Parceiro, ContaCorrente, CartaoCredito, LancamentoCartao
from .schemas import (
    ContaCreate, ContaUpdate, UsuarioCreate, CategoriaCreate, ParceiroCreate,
    ContaCorrenteCreate, ContaCorrenteUpdate, ContaBaixa,
    CartaoCreditoCreate, LancamentoCartaoCreate, FechamentoFaturaRequest
)
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

# ==========================================
# SERVIÇOS DE CARTÃO DE CRÉDITO
# ==========================================
class CartaoCreditoService:
    @staticmethod
    def listar(db: Session, usuario_id: int):
        return db.query(CartaoCredito).filter(CartaoCredito.usuario_id == usuario_id).all()

    @staticmethod
    def obter(db: Session, cartao_id: int, usuario_id: int):
        return db.query(CartaoCredito).filter(
            CartaoCredito.id == cartao_id,
            CartaoCredito.usuario_id == usuario_id
        ).first()

    @staticmethod
    def criar(db: Session, dados: CartaoCreditoCreate, usuario_id: int):
        # Validar que a conta corrente existe e pertence ao usuário
        db_cc = db.query(ContaCorrente).filter(
            ContaCorrente.id == dados.conta_corrente_id,
            ContaCorrente.usuario_id == usuario_id
        ).first()
        if not db_cc:
            raise HTTPException(
                status_code=400,
                detail="Conta corrente não encontrada ou não pertence ao usuário"
            )

        db_cartao = CartaoCredito(
            nome=dados.nome,
            limite=dados.limite,
            dia_fechamento=dados.dia_fechamento,
            dia_vencimento=dados.dia_vencimento,
            usuario_id=usuario_id,
            conta_corrente_id=dados.conta_corrente_id
        )
        db.add(db_cartao)
        db.commit()
        db.refresh(db_cartao)
        return db_cartao

    @staticmethod
    def fechar_fatura(db: Session, cartao_id: int, dados: FechamentoFaturaRequest, usuario_id: int):
        """Fecha a fatura do cartão: soma lançamentos e cria uma Conta a Pagar."""
        # Buscar o cartão
        db_cartao = db.query(CartaoCredito).filter(
            CartaoCredito.id == cartao_id,
            CartaoCredito.usuario_id == usuario_id
        ).first()
        if not db_cartao:
            raise HTTPException(status_code=404, detail="Cartão não encontrado")

        # Verificar se já existe fatura fechada para este mês/ano
        descricao_fatura = f"Fatura Cartão {db_cartao.nome} - {dados.mes:02d}/{dados.ano}"
        fatura_existente = db.query(Conta).filter(
            Conta.descricao == descricao_fatura,
            Conta.usuario_id == usuario_id
        ).first()
        if fatura_existente:
            raise HTTPException(
                status_code=400,
                detail=f"Fatura de {dados.mes:02d}/{dados.ano} já foi fechada para este cartão"
            )

        # Somar os lançamentos do mês/ano
        total = db.query(func.sum(LancamentoCartao.valor)).filter(
            LancamentoCartao.cartao_id == cartao_id,
            LancamentoCartao.mes_fatura == dados.mes,
            LancamentoCartao.ano_fatura == dados.ano,
            LancamentoCartao.usuario_id == usuario_id
        ).scalar()

        if not total or total == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Não há lançamentos para o cartão no período {dados.mes:02d}/{dados.ano}"
            )

        # Calcular data de vencimento
        # Se o dia_vencimento cai no mês seguinte ao fechamento
        mes_vencimento = dados.mes + 1 if dados.mes < 12 else 1
        ano_vencimento = dados.ano if dados.mes < 12 else dados.ano + 1

        # Ajustar dia de vencimento para meses com menos dias
        import calendar
        ultimo_dia = calendar.monthrange(ano_vencimento, mes_vencimento)[1]
        dia_venc = min(db_cartao.dia_vencimento, ultimo_dia)

        data_vencimento = date(ano_vencimento, mes_vencimento, dia_venc)

        # Criar a Conta a Pagar
        db_conta = Conta(
            descricao=descricao_fatura,
            valor=total,
            data_vencimento=data_vencimento,
            tipo="PAGAR",
            status="Pendente",
            usuario_id=usuario_id
        )
        db.add(db_conta)
        db.commit()
        db.refresh(db_conta)
        return db_conta

# ==========================================
# SERVIÇOS DE LANÇAMENTO DE CARTÃO
# ==========================================
class LancamentoCartaoService:
    @staticmethod
    def criar(db: Session, cartao_id: int, dados: LancamentoCartaoCreate, usuario_id: int):
        # Verificar se o cartão existe e pertence ao usuário
        db_cartao = db.query(CartaoCredito).filter(
            CartaoCredito.id == cartao_id,
            CartaoCredito.usuario_id == usuario_id
        ).first()
        if not db_cartao:
            raise HTTPException(status_code=404, detail="Cartão não encontrado")

        db_lancamento = LancamentoCartao(
            descricao=dados.descricao,
            valor=dados.valor,
            data_compra=dados.data_compra,
            mes_fatura=dados.mes_fatura,
            ano_fatura=dados.ano_fatura,
            cartao_id=cartao_id,
            categoria_id=dados.categoria_id,
            usuario_id=usuario_id
        )
        db.add(db_lancamento)
        db.commit()
        db.refresh(db_lancamento)
        return db_lancamento

    @staticmethod
    def listar(
        db: Session,
        cartao_id: int,
        usuario_id: int,
        mes_fatura: int = None,
        ano_fatura: int = None
    ):
        query = db.query(LancamentoCartao).filter(
            LancamentoCartao.cartao_id == cartao_id,
            LancamentoCartao.usuario_id == usuario_id
        )
        if mes_fatura is not None:
            query = query.filter(LancamentoCartao.mes_fatura == mes_fatura)
        if ano_fatura is not None:
            query = query.filter(LancamentoCartao.ano_fatura == ano_fatura)
        return query.all()
