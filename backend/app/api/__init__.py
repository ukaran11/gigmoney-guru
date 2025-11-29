"""
GigMoney Guru - API Package
"""
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.state import router as state_router
from app.api.agents import router as agents_router
from app.api.advances import router as advances_router
from app.api.goals import router as goals_router
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.api.demo import router as demo_router
from app.api.income import router as income_router
from app.api.expenses import router as expenses_router
from app.api.obligations import router as obligations_router

__all__ = [
    "auth_router",
    "user_router",
    "state_router",
    "agents_router",
    "advances_router",
    "goals_router",
    "chat_router",
    "admin_router",
    "demo_router",
    "income_router",
    "expenses_router",
    "obligations_router",
]
