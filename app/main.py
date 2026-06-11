from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Tambahkan import ini
from app.api.routes import chat
from app.db.database import engine, Base, SessionLocal
from app.db.seed import seed_database

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Core Business Intelligence AI Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Core Chat AI Engine"])

@app.on_event("startup")
def application_startup_lifecycle():
    db_session = SessionLocal()
    try:
        seed_database(db_session)
    finally:
        db_session.close()

@app.get("/", tags=["Health Check"])
def check_system_health():
    return {"status": "healthy", "message": "Application is running smoothly."}