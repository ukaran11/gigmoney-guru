"""
GigMoney Guru - Database Connection
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings

# Import all document models
from app.models.user import User
from app.models.income import IncomeEvent
from app.models.expense import ExpenseEvent
from app.models.obligation import Obligation
from app.models.bucket import Bucket
from app.models.goal import Goal
from app.models.advance import MicroAdvance
from app.models.decision import AgentDecision
from app.models.chat import ChatMessage
from app.models.platform_account import PlatformAccount


class Database:
    client: AsyncIOMotorClient = None
    

db = Database()


async def connect_to_database():
    """Initialize database connection and Beanie ODM."""
    db.client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Get database name from URI or default
    db_name = "gigmoney"
    if "/" in settings.mongodb_uri:
        parts = settings.mongodb_uri.split("/")
        if len(parts) > 3:
            db_name = parts[-1].split("?")[0] or "gigmoney"
    
    await init_beanie(
        database=db.client[db_name],
        document_models=[
            User,
            PlatformAccount,
            IncomeEvent,
            ExpenseEvent,
            Obligation,
            Bucket,
            Goal,
            MicroAdvance,
            AgentDecision,
            ChatMessage,
        ]
    )
    print(f"✅ Connected to MongoDB: {db_name}")


async def close_database_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        print("❌ Disconnected from MongoDB")
