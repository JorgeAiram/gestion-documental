import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.routes import (
    auth,
    users,
    folders,
    files,
    versions,
    comments,
    reviews,
    notifications,
    audit,
    shares,
    backup,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database and seeds
    init_db()
    yield

app = FastAPI(
    title="Plataforma Web de Gestión Documental con Control de Versiones",
    description="API REST corporativa para sustitución de carpetas compartidas en red, con control inmutable de versiones, bloqueo por concurrencia, permisos por rol, auditoría y respaldos.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(versions.router)
app.include_router(comments.router)
app.include_router(reviews.router)
app.include_router(notifications.router)
app.include_router(audit.router)
app.include_router(shares.router)
app.include_router(backup.router)

# Frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Plataforma de Gestión Documental en ejecución.</h2><p><a href='/docs'>Ver Swagger API Docs</a></p>")

@app.get("/share/{token}", response_class=HTMLResponse)
async def serve_share_page(token: str):
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Enlace Compartido</h2>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
