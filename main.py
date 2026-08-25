from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base
from config import CORS_ORIGINS
from seed import seed
from routes import auth, instruments, verification, certificates, dashboard, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed()
    yield


app = FastAPI(
    title="SIH26036 - Weighing & Measuring Instruments Verification System",
    description=(
        "Online verification system for weighing and measuring instruments. "
        "Supports instrument registration, verification workflow, certificate "
        "generation, QR-based public verification, and admin dashboard. "
        "Built for Smart India Hackathon 2026."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(instruments.router)
app.include_router(verification.router)
app.include_router(certificates.router)
app.include_router(dashboard.router)
app.include_router(public.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "SIH26036 Verification Backend"}


@app.get("/")
def read_root():
    return {"message": "Backend is running!", "docs": "/docs"}
