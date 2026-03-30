from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import contas, auth, categorias, parceiros, contas_correntes, cartoes, notificacoes, relatorios

# Cria as tabelas no banco de dados (se não existirem)
Base.metadata.create_all(bind=engine)

tags_metadata = [
    {
        "name": "Autenticação",
        "description": "Operações de login e registro de usuários.",
    },
    {
        "name": "Cartões de Crédito",
        "description": "Gerenciamento de cartões de crédito, lançamentos e fechamento de faturas.",
    },
    {
        "name": "Contas",
        "description": "Gerenciamento de contas a pagar e receber, incluindo a rotina de baixa.",
    },
    {
        "name": "Contas Correntes",
        "description": "Gerenciamento das contas correntes utilizadas para o controle de saldos.",
    },
    {
        "name": "Categorias",
        "description": "Classificação e organização das transações.",
    },
    {
        "name": "Parceiros",
        "description": "Gerenciamento de clientes e fornecedores associados às contas.",
    },
    {
        "name": "Notificações",
        "description": "Sistema de alertas para contas vencidas e fechamento de faturas de cartões.",
    },
    {
        "name": "Relatórios",
        "description": (
            "Relatórios financeiros: contas a pagar/receber, contas pagas/recebidas, "
            "extrato por conta corrente, agrupamento por categoria e fatura de cartão."
        ),
    },
]

app = FastAPI(
    title="API de Controle Financeiro",
    description="API para gerenciamento completo de finanças pessoais (contas, cartões, saldos).",
    version="1.0.0",
    openapi_tags=tags_metadata
)

# BUG 4 FIX — CORS configurado ANTES dos routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # ajuste para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas
app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(parceiros.router)
app.include_router(contas_correntes.router)
app.include_router(cartoes.router)
app.include_router(contas.router)
app.include_router(notificacoes.router)
app.include_router(relatorios.router)

@app.get("/")
def root():
    return {"message": "Bem-vindo à API de Controle Financeiro. Acesse /docs para a documentação."}