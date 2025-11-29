"""
GigMoney Guru - Main FastAPI Application

Entry point for the backend API.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import connect_to_database, close_database_connection
from app.api import (
    auth_router,
    user_router,
    state_router,
    agents_router,
    advances_router,
    goals_router,
    chat_router,
    admin_router,
    demo_router,
    income_router,
    expenses_router,
    obligations_router,
)
from app.api.charts import router as charts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting GigMoney Guru API...")
    await connect_to_database()
    print("✅ Database connected")
    yield
    # Shutdown
    print("👋 Shutting down GigMoney Guru API...")
    await close_database_connection()


# Create FastAPI app
app = FastAPI(
    title="GigMoney Guru API",
    description="""
    🎯 AI-Powered Financial Coach for Gig Workers
    
    GigMoney Guru helps gig workers in India manage their irregular income
    through intelligent bucket allocation, expense tracking, micro-advances,
    and personalized coaching in Hindi/Hinglish.
    
    ## Features
    
    - **Smart Buckets**: Auto-allocate earnings to rent, EMI, savings, etc.
    - **Income Tracking**: Connect Uber, Ola, Swiggy, and more
    - **Micro-Advances**: Low-interest advances for emergencies
    - **AI Coaching**: Bilingual chat-based financial guidance
    - **Goal Setting**: Track progress on savings goals
    
    ## Authentication
    
    All endpoints except `/auth/*` require a Bearer token.
    Get your token from `/auth/login`.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # Production URLs (Render)
        "https://gigmoney-guru-react.onrender.com",
        "https://gigmoney-guru-fastapi.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(state_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(advances_router, prefix="/api")
app.include_router(goals_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(income_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
app.include_router(obligations_router, prefix="/api")
app.include_router(charts_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "GigMoney Guru API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
