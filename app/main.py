from fastapi import FastAPI
from .database import engine, Base
from .routers import contas, auth, categorias, parceiros

# Cria as tabelas no banco de dados (se não existirem)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Controle Financeiro",
    description="API para gerenciamento de contas a pagar",
    version="1.0.0"
)

# Inclui as rotas
app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(parceiros.router)
app.include_router(contas.router)

@app.get("/")
def root():
    return {"message": "Bem-vindo à API de Controle Financeiro. Acesse /docs para a documentação."}
