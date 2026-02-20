# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .routes_auth import router as auth_router
from .routes_content import router as content_router
from .uploads import router as upload_router
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run DB creation in background thread to avoid blocking
    await asyncio.to_thread(create_db_and_tables)
    yield
    print("Shutting down...")

app = FastAPI(title="Student Government CMS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(content_router)
app.include_router(upload_router)

@app.get("/")
async def home():
    return {"welcome": "Student Government CMS API", "version": "1.0.0"}