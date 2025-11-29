"""
GigMoney Guru - User API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from beanie import PydanticObjectId

from app.api.auth import get_current_user
from app.schemas.user import UserProfile, UserProfileUpdate, PlatformConnect
from app.models.user import User
from app.models.platform_account import PlatformAccount
from app.services.allocation import AllocationService


router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile."""
    return UserProfile(
        id=str(current_user.id),
        name=current_user.name,
        phone=current_user.phone,
        email=current_user.email,
        city=current_user.city,
        platforms_used=current_user.platforms_used,
        monthly_rent=current_user.monthly_rent,
        has_emi=current_user.has_emi,
        preferred_language=current_user.preferred_language,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at,
    )


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile."""
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = __import__('datetime').datetime.utcnow()
    await current_user.save()
    
    # If this is first profile update and onboarding is completed, create buckets
    if data.onboarding_completed and not await AllocationService.get_user_buckets(str(current_user.id)):
        await AllocationService.create_default_buckets(
            str(current_user.id),
            monthly_rent=current_user.monthly_rent,
            has_emi=current_user.has_emi,
        )
    
    return UserProfile(
        id=str(current_user.id),
        name=current_user.name,
        phone=current_user.phone,
        email=current_user.email,
        city=current_user.city,
        platforms_used=current_user.platforms_used,
        monthly_rent=current_user.monthly_rent,
        has_emi=current_user.has_emi,
        preferred_language=current_user.preferred_language,
        onboarding_completed=current_user.onboarding_completed,
        created_at=current_user.created_at,
    )


@router.post("/platforms/connect")
async def connect_platform(
    data: PlatformConnect,
    current_user: User = Depends(get_current_user)
):
    """Connect a gig platform (mock)."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    # Check if already connected
    existing = await PlatformAccount.find_one(
        PlatformAccount.user_id == user_oid,
        PlatformAccount.platform_name == data.platform_name
    )
    
    if existing:
        return {"message": "Platform already connected", "platform": data.platform_name}
    
    # Create platform account
    platform = PlatformAccount(
        user_id=user_oid,
        platform_name=data.platform_name,
        platform_type=data.platform_type,
        is_connected=True,
        mock_account_id=f"mock_{data.platform_name}_{str(current_user.id)[:8]}",
    )
    
    await platform.insert()
    
    # Update user's platforms_used
    if data.platform_name not in current_user.platforms_used:
        current_user.platforms_used.append(data.platform_name)
        await current_user.save()
    
    return {
        "message": f"Successfully connected to {data.platform_name}",
        "platform": data.platform_name,
        "platform_type": data.platform_type,
    }


@router.get("/platforms")
async def get_platforms(current_user: User = Depends(get_current_user)):
    """Get connected platforms."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    platforms = await PlatformAccount.find(
        PlatformAccount.user_id == user_oid
    ).to_list()
    
    return {
        "platforms": [
            {
                "id": str(p.id),
                "name": p.platform_name,
                "type": p.platform_type,
                "is_connected": p.is_connected,
                "connected_at": p.connected_at.isoformat(),
            }
            for p in platforms
        ]
    }


@router.delete("/platforms/{platform_name}")
async def disconnect_platform(
    platform_name: str,
    current_user: User = Depends(get_current_user)
):
    """Disconnect a platform."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    platform = await PlatformAccount.find_one(
        PlatformAccount.user_id == user_oid,
        PlatformAccount.platform_name == platform_name
    )
    
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not connected")
    
    await platform.delete()
    
    # Update user's platforms_used
    if platform_name in current_user.platforms_used:
        current_user.platforms_used.remove(platform_name)
        await current_user.save()
    
    return {"message": f"Disconnected from {platform_name}"}
