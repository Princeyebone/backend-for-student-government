# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .routes_auth import router as auth_router
from .routes_content import router as content_router
from .uploads import router as upload_router
from .routes_bills import router as bills_router
from .config import settings
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    try:
        print("Starting database setup...")
        print(f"DATABASE_URL configured: {'Yes' if settings.DATABASE_URL else 'No'}")
        
        # Run DB creation in background thread to avoid blocking
        await asyncio.to_thread(create_db_and_tables)
        print("Database tables created successfully!")
        
    except Exception as e:
        print(f"ERROR during database setup: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - let the app start anyway for debugging
        print("Continuing startup despite database error...")
    
    yield
    print("Shutting down...")

app = FastAPI(title="Student Government CMS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://student-government-website.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(content_router)
app.include_router(upload_router)
app.include_router(bills_router)

@app.get("/")
async def home():
    return {"welcome": "Student Government CMS API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    try:
        # Test database connection
        from .database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "config_loaded": bool(settings.DATABASE_URL)
    }