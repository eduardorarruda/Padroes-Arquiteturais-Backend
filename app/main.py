from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import contas, auth, categorias, parceiros, contas_correntes

# Cria as tabelas no banco de dados (se não existirem)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Controle Financeiro",
    description="API para gerenciamento de contas a pagar e receber",
    version="1.0.0"
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
app.include_router(contas.router)

@app.get("/")
def root():
    return {"message": "Bem-vindo à API de Controle Financeiro. Acesse /docs para a documentação."}