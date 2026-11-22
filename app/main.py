"""Application FastAPI : CORS, routeurs et démarrage."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import livres


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # tables + livres de départ si la table est vide
    yield


app = FastAPI(
    title="API Bibliothèque",
    description="Backend du devoir 2 de LOG3550 : gestion de livres avec FastAPI et SQLite.",
    version="1.0.0",
    openapi_tags=[{"name": "Livres", "description": "Opérations CRUD sur les livres"},
                  {"name": "Système", "description": "Vérification de l'état de l'API"}],
    lifespan=lifespan,
)

# Origines du frontend, séparées par des virgules, modifiables sans toucher au code.
# Pas d'astérisque : seul le frontend du devoir 1 est autorisé.
ORIGINES = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINES,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
    expose_headers=["Location"],
)

app.include_router(livres.router)


@app.get("/sante", tags=["Système"], summary="État de l'API")
def sante():
    return {"statut": "ok"}
