"""
GigMoney Guru - API Schemas Package
"""
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenData,
)
from app.schemas.user import (
    UserProfile,
    UserProfileUpdate,
)
from app.schemas.state import (
    DailyState,
    ForecastDay,
    ForecastResponse,
    BucketState,
    AllocationPlan,
)
from app.schemas.advance import (
    AdvanceOffer,
    AdvanceAccept,
    AdvanceStatus,
)
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    ScenarioRequest,
    ScenarioResponse,
)
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    QuickReplyButton,
)
from app.schemas.context import FinancialContext

__all__ = [
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenData",
    "UserProfile",
    "UserProfileUpdate",
    "DailyState",
    "ForecastDay",
    "ForecastResponse",
    "BucketState",
    "AllocationPlan",
    "AdvanceOffer",
    "AdvanceAccept",
    "AdvanceStatus",
    "GoalCreate",
    "GoalUpdate",
    "GoalResponse",
    "ScenarioRequest",
    "ScenarioResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "QuickReplyButton",
    "FinancialContext",
]
