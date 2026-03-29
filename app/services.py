from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from fastapi import HTTPException
from datetime import date, datetime
from .models import Conta, Usuario, Categoria, Parceiro, ContaCorrente, CartaoCredito, LancamentoCartao, Notificacao
from .schemas import (
    ContaCreate, ContaUpdate, UsuarioCreate, CategoriaCreate, ParceiroCreate,
    ContaCorrenteCreate, ContaCorrenteUpdate, ContaBaixa, TransferenciaRequest,
    CartaoCreditoCreate, CartaoCreditoUpdate, LancamentoCartaoCreate, FechamentoFaturaRequest
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
    def _buscar_dados_cnpj(cnpj: str) -> dict:
        """Consulta a BrasilAPI e retorna os dados mapeados, ou {} em caso de falha."""
        import httpx
        cnpj_numerico = "".join(filter(str.isdigit, cnpj))
        try:
            response = httpx.get(
                f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_numerico}",
                timeout=10.0
            )
            if response.status_code != 200:
                return {}
            dados = response.json()

            # Monta o endereço concatenando os campos disponíveis
            partes_endereco = filter(None, [
                dados.get("logradouro"),
                dados.get("numero"),
                dados.get("bairro"),
                dados.get("municipio"),
                dados.get("uf"),
            ])
            endereco = ", ".join(partes_endereco)

            # Converte data_inicio_atividade ("YYYY-MM-DD") para objeto date
            data_fundacao = None
            data_str = dados.get("data_inicio_atividade")
            if data_str:
                try:
                    from datetime import date as date_type
                    data_fundacao = date_type.fromisoformat(data_str)
                except ValueError:
                    pass

            return {
                "razao_social": dados.get("razao_social"),
                "nome_fantasia": dados.get("nome_fantasia") or None,
                "endereco": endereco or None,
                "data_nascimento_fundacao": data_fundacao,
            }
        except Exception:
            # Falha silenciosa: a criação do parceiro prossegue sem os dados da API
            return {}

    @staticmethod
    def _e_cnpj(cpf_cnpj: str) -> bool:
        """Retorna True se o valor tiver exatamente 14 dígitos numéricos (CNPJ)."""
        return len("".join(filter(str.isdigit, cpf_cnpj))) == 14

    @staticmethod
    def listar_parceiros(db: Session, usuario_id: int):
        return db.query(Parceiro).filter(Parceiro.usuario_id == usuario_id).all()

    @staticmethod
    def criar_parceiro(db: Session, parceiro: ParceiroCreate, usuario_id: int):
        dados = parceiro.dict() if hasattr(parceiro, "dict") else parceiro.model_dump()

        # Auto-preenchimento via CNPJ quando os campos de detalhe estiverem vazios
        cpf_cnpj = dados.get("cpf_cnpj") or ""
        campos_vazios = not dados.get("razao_social") and not dados.get("endereco")

        if cpf_cnpj and ParceiroService._e_cnpj(cpf_cnpj) and campos_vazios:
            dados_api = ParceiroService._buscar_dados_cnpj(cpf_cnpj)
            for campo, valor in dados_api.items():
                if valor is not None:
                    dados[campo] = valor

        db_parceiro = Parceiro(**dados, usuario_id=usuario_id)
        db.add(db_parceiro)
        db.commit()
        db.refresh(db_parceiro)
        return db_parceiro

    @staticmethod
    def atualizar_parceiro(db: Session, parceiro_id: int, dados_update: "ParceiroUpdate", usuario_id: int):
        par = db.query(Parceiro).filter(
            Parceiro.id == parceiro_id,
            Parceiro.usuario_id == usuario_id,
        ).first()
        if not par:
            return None

        dados = dados_update.dict(exclude_unset=True) if hasattr(dados_update, "dict") else dados_update.model_dump(exclude_unset=True)

        # Auto-preenchimento via CNPJ também na atualização
        cpf_cnpj = dados.get("cpf_cnpj") or getattr(par, "cpf_cnpj", "") or ""
        campos_vazios = not dados.get("razao_social") and not dados.get("endereco")

        if cpf_cnpj and ParceiroService._e_cnpj(cpf_cnpj) and campos_vazios:
            dados_api = ParceiroService._buscar_dados_cnpj(cpf_cnpj)
            for campo, valor in dados_api.items():
                if valor is not None and campo not in dados:
                    dados[campo] = valor

        for key, value in dados.items():
            setattr(par, key, value)

        db.commit()
        db.refresh(par)
        return par

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

    @staticmethod
    def transferir(db: Session, dados: TransferenciaRequest, usuario_id: int):
        if dados.conta_origem_id == dados.conta_destino_id:
            raise HTTPException(status_code=400, detail="A conta de origem não pode ser a mesma de destino.")

        # Buscar conta origem e bloquear para atualização
        conta_origem = db.query(ContaCorrente).filter(
            ContaCorrente.id == dados.conta_origem_id,
            ContaCorrente.usuario_id == usuario_id
        ).with_for_update().first()

        if not conta_origem:
            raise HTTPException(status_code=404, detail="Conta corrente de origem não encontrada.")

        # Buscar conta destino e bloquear para atualização
        conta_destino = db.query(ContaCorrente).filter(
            ContaCorrente.id == dados.conta_destino_id,
            ContaCorrente.usuario_id == usuario_id
        ).with_for_update().first()

        if not conta_destino:
            raise HTTPException(status_code=404, detail="Conta corrente de destino não encontrada.")

        if float(conta_origem.saldo) < dados.valor:
            raise HTTPException(status_code=400, detail="Saldo insuficiente na conta de origem.")

        try:
            # Subtrair do saldo de origem
            conta_origem.saldo = float(conta_origem.saldo) - dados.valor
            # Adicionar ao saldo de destino
            conta_destino.saldo = float(conta_destino.saldo) + dados.valor

            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Erro interno ao realizar transferência.")

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
        
        # Remove os campos virtuais do Pydantic para não darem erro no SQLAlchemy
        qtd_parcelas = conta_data.pop("quantidade_parcelas", 1)
        intervalo_meses = conta_data.pop("intervalo_meses", 1)
        dividir_valor = conta_data.pop("dividir_valor", False)
        
        # Validação para a conta original que nasça paga (geralmente só a primeira)
        status_atual = str(conta_data.get("status", "")).upper()
        if status_atual in ["PAGO", "RECEBIDO"]:
            if not conta_data.get("conta_corrente_id"):
                raise HTTPException(status_code=400, detail="É obrigatório informar a 'conta_corrente_id' quando a conta for criada com status PAGO ou RECEBIDO.")
            if not conta_data.get("data_pagamento"):
                raise HTTPException(status_code=400, detail="É obrigatório informar a 'data_pagamento' quando a conta for criada com status PAGO ou RECEBIDO.")
                
            # Validar conta corrente
            db_cc = db.query(ContaCorrente).filter(
                ContaCorrente.id == conta_data["conta_corrente_id"],
                ContaCorrente.usuario_id == usuario_id
            ).first()
            if not db_cc:
                raise HTTPException(status_code=400, detail="Conta corrente informada não encontrada ou não pertence ao usuário.")

        # Se for apenas 1 parcela, criar diretamente
        if qtd_parcelas <= 1:
            db_conta = Conta(**conta_data, usuario_id=usuario_id)
            db.add(db_conta)
            db.commit()
            db.refresh(db_conta)
            return db_conta

        import uuid
        import calendar
        from datetime import date
        
        grupo_uuid = str(uuid.uuid4())
        valor_original = float(conta_data.get("valor", 0))
        valor_parcela = round(valor_original / qtd_parcelas, 2) if dividir_valor else valor_original
        
        data_base_vencimento = conta_data.get("data_vencimento")
        descricao_base = conta_data.get("descricao", "")
        
        primeira_conta = None
        
        for i in range(1, qtd_parcelas + 1):
            dados_parcela = conta_data.copy()
            dados_parcela["grupo_parcelamento"] = grupo_uuid
            dados_parcela["numero_parcela"] = i
            dados_parcela["total_parcelas"] = qtd_parcelas
            dados_parcela["valor"] = valor_parcela
            dados_parcela["descricao"] = f"{descricao_base} ({i}/{qtd_parcelas})"
            
            # Ajuste de vencimento (exceto para a primeira parcela)
            if i > 1:
                meses_adicionais = (i - 1) * intervalo_meses
                novo_mes = data_base_vencimento.month + meses_adicionais
                ano_incremento = (novo_mes - 1) // 12
                mes_final = ((novo_mes - 1) % 12) + 1
                ano_final = data_base_vencimento.year + ano_incremento
                
                # Previne erro de dias que não existem no mês, ex: 31 Fev
                ultimo_dia_mes = calendar.monthrange(ano_final, mes_final)[1]
                dia_final = min(data_base_vencimento.day, ultimo_dia_mes)
                
                dados_parcela["data_vencimento"] = date(ano_final, mes_final, dia_final)
                
                # Limpar status de pagamento para parcelas futuras
                dados_parcela["status"] = "Pendente"
                dados_parcela["data_pagamento"] = None
                dados_parcela["conta_corrente_id"] = None
            
            db_conta = Conta(**dados_parcela, usuario_id=usuario_id)
            db.add(db_conta)
            
            if i == 1:
                primeira_conta = db_conta
                
        db.commit()
        db.refresh(primeira_conta)
        return primeira_conta

    @staticmethod
    def atualizar_conta(db: Session, conta_id: int, conta_update: ContaUpdate, usuario_id: int):
        db_conta = db.query(Conta).filter(Conta.id == conta_id, Conta.usuario_id == usuario_id).first()
        if not db_conta:
            return None

        update_data = conta_update.dict(exclude_unset=True) if hasattr(conta_update, 'dict') else conta_update.model_dump(exclude_unset=True)
        
        # Desvinculação da conta corrente e data de pagamento se o status voltar para PENDENTE
        if "status" in update_data and update_data["status"].upper() == "PENDENTE":
            db_conta.conta_corrente_id = None
            db_conta.data_pagamento = None
            
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

        # Vincular a conta corrente e registrar data_pagamento
        db_conta.conta_corrente_id = baixa.conta_corrente_id
        db_conta.data_pagamento = baixa.data_pagamento if baixa.data_pagamento else date.today()

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
    def _calcular_limites(db: Session, cartao: CartaoCredito, usuario_id: int):
        from sqlalchemy import func
        lancamentos_agrupados = db.query(
            LancamentoCartao.mes_fatura, 
            LancamentoCartao.ano_fatura, 
            func.sum(LancamentoCartao.valor).label("total")
        ).filter(
            LancamentoCartao.cartao_id == cartao.id,
            LancamentoCartao.usuario_id == usuario_id
        ).group_by(
            LancamentoCartao.mes_fatura, 
            LancamentoCartao.ano_fatura
        ).all()

        limite_usado = 0.0
        for mes, ano, total in lancamentos_agrupados:
            descricao_fatura = f"Fatura Cartão {cartao.nome} - {mes:02d}/{ano}"
            conta_paga = db.query(Conta).filter(
                Conta.descricao == descricao_fatura,
                Conta.usuario_id == usuario_id,
                Conta.status.in_(["Pago", "Recebido", "PAGO", "RECEBIDO"])
            ).first()
            
            if not conta_paga:
                limite_usado += float(total or 0.0)
                
        cartao.limite_usado = limite_usado
        cartao.limite_livre = float(cartao.limite) - limite_usado
        return cartao

    @staticmethod
    def listar(db: Session, usuario_id: int):
        cartoes = db.query(CartaoCredito).filter(CartaoCredito.usuario_id == usuario_id).all()
        return [CartaoCreditoService._calcular_limites(db, c, usuario_id) for c in cartoes]

    @staticmethod
    def obter(db: Session, cartao_id: int, usuario_id: int):
        cartao = db.query(CartaoCredito).filter(
            CartaoCredito.id == cartao_id,
            CartaoCredito.usuario_id == usuario_id
        ).first()
        if cartao:
            return CartaoCreditoService._calcular_limites(db, cartao, usuario_id)
        return None

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
        return CartaoCreditoService._calcular_limites(db, db_cartao, usuario_id)

    @staticmethod
    def atualizar(db: Session, cartao_id: int, dados: CartaoCreditoUpdate, usuario_id: int):
        db_cartao = db.query(CartaoCredito).filter(
            CartaoCredito.id == cartao_id,
            CartaoCredito.usuario_id == usuario_id
        ).first()

        if not db_cartao:
            raise HTTPException(status_code=404, detail="Cartão de crédito não encontrado")

        # Se for atualizar a conta corrente, validar se ela existe e pertence ao usuário
        if dados.conta_corrente_id is not None:
            db_cc = db.query(ContaCorrente).filter(
                ContaCorrente.id == dados.conta_corrente_id,
                ContaCorrente.usuario_id == usuario_id
            ).first()
            if not db_cc:
                raise HTTPException(
                    status_code=400,
                    detail="Nova conta corrente não encontrada ou não pertence ao usuário"
                )

        update_data = dados.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_cartao, key, value)

        db.commit()
        db.refresh(db_cartao)
        return CartaoCreditoService._calcular_limites(db, db_cartao, usuario_id)

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

        lancamento_data = dados.dict() if hasattr(dados, 'dict') else dados.model_dump()
        qtd_parcelas = lancamento_data.pop("quantidade_parcelas", 1)
        dividir_valor = lancamento_data.pop("dividir_valor", False)

        if qtd_parcelas <= 1:
            db_lancamento = LancamentoCartao(**lancamento_data, cartao_id=cartao_id, usuario_id=usuario_id)
            db.add(db_lancamento)
            db.commit()
            db.refresh(db_lancamento)
            return db_lancamento

        import uuid
        grupo_uuid = str(uuid.uuid4())
        valor_original = float(lancamento_data.get("valor", 0))
        valor_parcela = round(valor_original / qtd_parcelas, 2) if dividir_valor else valor_original
        
        mes_fatura_base = lancamento_data.get("mes_fatura")
        ano_fatura_base = lancamento_data.get("ano_fatura")
        descricao_base = lancamento_data.get("descricao", "")
        
        primeiro_lancamento = None
        
        for i in range(1, qtd_parcelas + 1):
            dados_parcela = lancamento_data.copy()
            dados_parcela["grupo_parcelamento"] = grupo_uuid
            dados_parcela["numero_parcela"] = i
            dados_parcela["total_parcelas"] = qtd_parcelas
            dados_parcela["valor"] = valor_parcela
            dados_parcela["descricao"] = f"{descricao_base} ({i}/{qtd_parcelas})"
            
            # Cálculo do mês/ano da fatura
            meses_avanco = i - 1
            mes_novo = mes_fatura_base + meses_avanco
            ano_adicional = (mes_novo - 1) // 12
            mes_final = ((mes_novo - 1) % 12) + 1
            ano_final = ano_fatura_base + ano_adicional
            
            dados_parcela["mes_fatura"] = mes_final
            dados_parcela["ano_fatura"] = ano_final
            
            db_lancamento = LancamentoCartao(**dados_parcela, cartao_id=cartao_id, usuario_id=usuario_id)
            db.add(db_lancamento)
            
            if i == 1:
                primeiro_lancamento = db_lancamento
                
        db.commit()
        db.refresh(primeiro_lancamento)
        return primeiro_lancamento

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

    @staticmethod
    def atualizar(
        db: Session,
        lancamento_id: int,
        cartao_id: int,
        dados: "LancamentoCartaoUpdate",
        usuario_id: int,
    ):
        """Atualiza campos permitidos de um lançamento sem alterar fatura ou cartão."""
        db_lancamento = db.query(LancamentoCartao).filter(
            LancamentoCartao.id == lancamento_id,
            LancamentoCartao.cartao_id == cartao_id,
            LancamentoCartao.usuario_id == usuario_id,
        ).first()
        if not db_lancamento:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")

        update_data = (
            dados.dict(exclude_unset=True)
            if hasattr(dados, "dict")
            else dados.model_dump(exclude_unset=True)
        )
        for key, value in update_data.items():
            setattr(db_lancamento, key, value)

        db.commit()
        db.refresh(db_lancamento)
        return db_lancamento

    @staticmethod
    def deletar(
        db: Session,
        lancamento_id: int,
        cartao_id: int,
        usuario_id: int,
    ):
        """Remove um lançamento do banco de dados."""
        db_lancamento = db.query(LancamentoCartao).filter(
            LancamentoCartao.id == lancamento_id,
            LancamentoCartao.cartao_id == cartao_id,
            LancamentoCartao.usuario_id == usuario_id,
        ).first()
        if not db_lancamento:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")

        db.delete(db_lancamento)
        db.commit()
        return True

# ==========================================
# SERVIÇOS DE NOTIFICAÇÃO
# ==========================================
class NotificacaoService:
    @staticmethod
    def listar_nao_lidas(db: Session, usuario_id: int):
        """Retorna todas as notificações não lidas do usuário."""
        return (
            db.query(Notificacao)
            .filter(
                Notificacao.usuario_id == usuario_id,
                Notificacao.lida == False
            )
            .order_by(Notificacao.data_criacao.desc())
            .all()
        )

    @staticmethod
    def marcar_como_lida(db: Session, notificacao_id: int, usuario_id: int):
        """Marca uma notificação como lida."""
        db_notificacao = db.query(Notificacao).filter(
            Notificacao.id == notificacao_id,
            Notificacao.usuario_id == usuario_id
        ).first()
        if not db_notificacao:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")

        db_notificacao.lida = True
        db.commit()
        db.refresh(db_notificacao)
        return db_notificacao

    @staticmethod
    def sincronizar_notificacoes(db: Session, usuario_id: int):
        """Verifica e gera alertas de contas vencidas e fechamento de fatura."""
        hoje = date.today()
        notificacoes_criadas = []

        # -----------------------------------------------
        # REGRA 1: Contas vencidas (Pendente + vencida)
        # -----------------------------------------------
        contas_vencidas = db.query(Conta).filter(
            Conta.usuario_id == usuario_id,
            Conta.status == "Pendente",
            Conta.data_vencimento < hoje
        ).all()

        for conta in contas_vencidas:
            # Alterar status para Atrasado
            conta.status = "Atrasado"

            # Verificar se já existe notificação para esta conta
            notif_existente = db.query(Notificacao).filter(
                Notificacao.usuario_id == usuario_id,
                Notificacao.tipo == "VENCIMENTO",
                Notificacao.referencia_id == conta.id
            ).first()

            if not notif_existente:
                data_formatada = conta.data_vencimento.strftime("%d/%m/%Y")
                nova_notif = Notificacao(
                    mensagem=f"A conta '{conta.descricao}' venceu no dia {data_formatada}.",
                    tipo="VENCIMENTO",
                    referencia_id=conta.id,
                    usuario_id=usuario_id
                )
                db.add(nova_notif)
                notificacoes_criadas.append(nova_notif)

        # -----------------------------------------------
        # REGRA 2: Fechamento de fatura de cartões
        # -----------------------------------------------
        cartoes = db.query(CartaoCredito).filter(
            CartaoCredito.usuario_id == usuario_id
        ).all()

        for cartao in cartoes:
            if cartao.dia_fechamento <= hoje.day:
                # Verificar se já existe notificação de FATURA para este cartão no mês atual
                notif_fatura_existente = db.query(Notificacao).filter(
                    Notificacao.usuario_id == usuario_id,
                    Notificacao.tipo == "FATURA",
                    Notificacao.referencia_id == cartao.id,
                    extract('month', Notificacao.data_criacao) == hoje.month,
                    extract('year', Notificacao.data_criacao) == hoje.year
                ).first()

                if not notif_fatura_existente:
                    nova_notif = Notificacao(
                        mensagem=f"A fatura do cartão '{cartao.nome}' fechou. Não se esqueça de lançar o fechamento.",
                        tipo="FATURA",
                        referencia_id=cartao.id,
                        usuario_id=usuario_id
                    )
                    db.add(nova_notif)
                    notificacoes_criadas.append(nova_notif)

        db.commit()

        # Refresh para retornar os IDs gerados
        for notif in notificacoes_criadas:
            db.refresh(notif)

        return notificacoes_criadas
