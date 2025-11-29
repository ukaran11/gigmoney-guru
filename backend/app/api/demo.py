"""
GigMoney Guru - Demo API

Seed demo data and run demo scenarios.
Implements "Ravi's Week" - the hackathon demo scenario.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from beanie import PydanticObjectId
import random

from app.api.auth import get_current_user
from app.models.user import User
from app.models.income import IncomeEvent
from app.models.expense import ExpenseEvent
from app.models.obligation import Obligation
from app.models.bucket import Bucket
from app.models.goal import Goal
from app.models.advance import MicroAdvance
from app.models.platform_account import PlatformAccount

# Seed random with current time for unique data each time
import time
random.seed(int(time.time()))

router = APIRouter(prefix="/demo", tags=["Demo"])


async def clear_user_data(user_id: PydanticObjectId):
    """Clear all financial data for a user."""
    await IncomeEvent.find(IncomeEvent.user_id == user_id).delete()
    await ExpenseEvent.find(ExpenseEvent.user_id == user_id).delete()
    await Obligation.find(Obligation.user_id == user_id).delete()
    await Bucket.find(Bucket.user_id == user_id).delete()
    await Goal.find(Goal.user_id == user_id).delete()
    await MicroAdvance.find(MicroAdvance.user_id == user_id).delete()
    await PlatformAccount.find(PlatformAccount.user_id == user_id).delete()


@router.post("/seed-ravi")
async def seed_ravi_demo(
    current_user: User = Depends(get_current_user)
):
    """
    Seed "Ravi's Week" demo data.
    
    Ravi is a multi-platform gig worker in Bangalore:
    - Drives for Uber and Ola
    - Delivers for Swiggy
    - Has variable income based on weather, festivals, and demand
    - Rent due on 5th of each month
    - Saving for his daughter's school fees
    """
    user_oid = PydanticObjectId(str(current_user.id))
    
    # Clear existing data
    await clear_user_data(user_oid)
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create platform accounts
    platforms = [
        PlatformAccount(
            user_id=user_oid,
            platform_name="Uber",
            platform_type="rideshare",
            account_id="uber_ravi_123",
            is_active=True,
            connected_at=today - timedelta(days=90),
        ),
        PlatformAccount(
            user_id=user_oid,
            platform_name="Ola",
            platform_type="rideshare",
            account_id="ola_ravi_456",
            is_active=True,
            connected_at=today - timedelta(days=60),
        ),
        PlatformAccount(
            user_id=user_oid,
            platform_name="Swiggy",
            platform_type="delivery",
            account_id="swiggy_ravi_789",
            is_active=True,
            connected_at=today - timedelta(days=45),
        ),
    ]
    for p in platforms:
        await p.save()
    
    # Create income events for the past 14 days
    income_data = []
    for days_ago in range(14, -1, -1):
        date = today - timedelta(days=days_ago)
        day_of_week = date.weekday()
        
        # Weekend = higher earnings
        is_weekend = day_of_week >= 5
        multiplier = 1.3 if is_weekend else 1.0
        
        # Simulate rain on some days (lower earnings)
        is_rainy = random.random() < 0.2
        if is_rainy:
            multiplier *= 0.6
        
        # Uber earnings (vary whether they drive Uber each day)
        if random.random() > 0.15:  # 85% chance of driving Uber
            uber_base = random.randint(350, 900)
            uber_amount = int(uber_base * multiplier)
            income_data.append(IncomeEvent(
                user_id=user_oid,
                source_type="platform",
                source_name="uber",
                platform_type="rides",
                amount=uber_amount,
                currency="INR",
                earned_at=date,
                description=f"Uber rides - {'Weekend rush' if is_weekend else 'Regular day'}",
            ))
        
        # Ola earnings (random days, not just alternating)
        if random.random() > 0.4:
            ola_base = random.randint(300, 600)
            ola_amount = int(ola_base * multiplier)
            income_data.append(IncomeEvent(
                user_id=user_oid,
                source_type="platform",
                source_name="ola",
                platform_type="rides",
                amount=ola_amount,
                currency="INR",
                earned_at=date,
                description="Ola rides",
            ))
        
        # Swiggy earnings (evening deliveries)
        if random.random() > 0.3:
            swiggy_base = random.randint(200, 400)
            swiggy_amount = int(swiggy_base * (1.2 if is_weekend else 1.0))
            income_data.append(IncomeEvent(
                user_id=user_oid,
                source_type="platform",
                source_name="swiggy",
                platform_type="food_delivery",
                amount=swiggy_amount,
                currency="INR",
                earned_at=date,
                description="Evening deliveries",
            ))
    
    for income in income_data:
        await income.save()
    
    # Create expense events
    expense_data = [
        # Recurring
        ExpenseEvent(user_id=user_oid, category="fuel", amount=500, spent_at=today - timedelta(days=1), description="Petrol"),
        ExpenseEvent(user_id=user_oid, category="fuel", amount=450, spent_at=today - timedelta(days=3), description="Petrol"),
        ExpenseEvent(user_id=user_oid, category="fuel", amount=520, spent_at=today - timedelta(days=6), description="Petrol"),
        ExpenseEvent(user_id=user_oid, category="food", amount=80, spent_at=today - timedelta(days=0), description="Lunch"),
        ExpenseEvent(user_id=user_oid, category="food", amount=120, spent_at=today - timedelta(days=1), description="Lunch + tea"),
        ExpenseEvent(user_id=user_oid, category="food", amount=200, spent_at=today - timedelta(days=2), description="Family dinner"),
        ExpenseEvent(user_id=user_oid, category="phone", amount=299, spent_at=today - timedelta(days=10), description="Jio recharge"),
        ExpenseEvent(user_id=user_oid, category="vehicle", amount=350, spent_at=today - timedelta(days=8), description="Bike service"),
    ]
    for exp in expense_data:
        await exp.save()
    
    # Create obligations
    obligations = [
        Obligation(
            user_id=user_oid,
            name="Room Rent",
            amount=8000,
            due_day=5,
            frequency="monthly",
            category="rent",
            bucket_name="essentials",
        ),
        Obligation(
            user_id=user_oid,
            name="Bike EMI",
            amount=3500,
            due_day=15,
            frequency="monthly",
            category="emi",
            bucket_name="essentials",
        ),
        Obligation(
            user_id=user_oid,
            name="Mobile Bill",
            amount=299,
            due_day=25,
            frequency="monthly",
            category="phone",
            bucket_name="essentials",
        ),
    ]
    for ob in obligations:
        await ob.save()
    
    # Create buckets
    total_income = sum(i.amount for i in income_data[-7:])  # Last 7 days
    
    buckets = [
        Bucket(
            user_id=user_oid,
            name="essentials",
            display_name="Essentials 🏠",
            icon="🏠",
            color="#FF9800",
            target_amount=8000,
            current_balance=int(total_income * 0.35),
            allocation_type="percentage",
            allocation_value=50,
            priority=1,
        ),
        Bucket(
            user_id=user_oid,
            name="flex",
            display_name="Flex 🛒",
            icon="🛒",
            color="#4CAF50",
            target_amount=0,
            current_balance=int(total_income * 0.20),
            allocation_type="percentage",
            allocation_value=30,
            priority=2,
        ),
        Bucket(
            user_id=user_oid,
            name="goals",
            display_name="Goals 🎯",
            icon="🎯",
            color="#2196F3",
            target_amount=15000,
            current_balance=int(total_income * 0.10),
            allocation_type="percentage",
            allocation_value=15,
            priority=3,
        ),
        Bucket(
            user_id=user_oid,
            name="emergency",
            display_name="Emergency 🆘",
            icon="🆘",
            color="#F44336",
            target_amount=10000,
            current_balance=2500,
            allocation_type="percentage",
            allocation_value=5,
            priority=4,
        ),
    ]
    for b in buckets:
        await b.save()
    
    # Create goals
    goals = [
        Goal(
            user_id=user_oid,
            name="School Fees",
            description="Daughter's school fees for next quarter",
            icon="📚",
            target_amount=15000,
            current_amount=4500,
            target_date=today + timedelta(days=45),
            monthly_contribution=3000,
            priority=1,
            status="active",
        ),
        Goal(
            user_id=user_oid,
            name="New Phone",
            description="Upgrade to a better smartphone",
            icon="📱",
            target_amount=12000,
            current_amount=2000,
            target_date=today + timedelta(days=90),
            monthly_contribution=2000,
            priority=2,
            status="active",
        ),
        Goal(
            user_id=user_oid,
            name="Diwali Gifts",
            description="Gifts for family and friends",
            icon="🪔",
            target_amount=5000,
            current_amount=800,
            target_date=today + timedelta(days=60),
            monthly_contribution=1500,
            priority=3,
            status="active",
        ),
    ]
    for g in goals:
        await g.save()
    
    # Update user profile
    current_user.name = current_user.name or "Ravi Kumar"
    current_user.preferred_language = "hinglish"
    current_user.onboarding_completed = True
    current_user.updated_at = datetime.now()
    await current_user.save()
    
    return {
        "success": True,
        "message": "Ravi's demo data seeded successfully!",
        "summary": {
            "platforms": len(platforms),
            "income_events": len(income_data),
            "expenses": len(expense_data),
            "obligations": len(obligations),
            "buckets": len(buckets),
            "goals": len(goals),
            "total_income_14d": sum(i.amount for i in income_data),
        }
    }


@router.post("/simulate-day")
async def simulate_day(
    scenario: str = "normal",
    current_user: User = Depends(get_current_user)
):
    """
    Simulate a day with different scenarios.
    
    Scenarios:
    - normal: Regular gig work day
    - rain: Rainy day (less rides, more deliveries)
    - festival: High demand day (Diwali, etc.)
    - emergency: Unexpected expense
    - payday: Multiple platform payouts
    """
    user_oid = PydanticObjectId(str(current_user.id))
    today = datetime.now()
    
    events = []
    
    if scenario == "normal":
        # Normal day
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="uber",
            platform_type="rides",
            amount=random.randint(500, 700),
            earned_at=today,
            description="Morning rides",
        ))
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="swiggy",
            platform_type="food_delivery",
            amount=random.randint(200, 350),
            earned_at=today,
            description="Evening deliveries",
        ))
        
    elif scenario == "rain":
        # Rainy day - less rideshare, more delivery
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="uber",
            platform_type="rides",
            amount=random.randint(200, 350),
            earned_at=today,
            description="Rainy day - few rides",
        ))
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="swiggy",
            platform_type="food_delivery",
            amount=random.randint(400, 600),
            earned_at=today,
            description="Rainy day surge - high delivery demand!",
        ))
        
    elif scenario == "festival":
        # Festival day - high demand
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="uber",
            platform_type="rides",
            amount=random.randint(1000, 1500),
            earned_at=today,
            description="Festival surge pricing!",
        ))
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="ola",
            platform_type="rides",
            amount=random.randint(600, 900),
            earned_at=today,
            description="Festival rides",
        ))
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="swiggy",
            platform_type="food_delivery",
            amount=random.randint(500, 700),
            earned_at=today,
            description="Festival food orders",
        ))
        
    elif scenario == "emergency":
        # Emergency expense
        events.append(ExpenseEvent(
            user_id=user_oid,
            category="health",
            amount=random.randint(1500, 3000),
            spent_at=today,
            description="Medical emergency - clinic visit",
        ))
        
    elif scenario == "payday":
        # Multiple platform payouts
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="uber",
            platform_type="rides",
            amount=random.randint(3000, 5000),
            earned_at=today,
            description="Weekly payout",
        ))
        events.append(IncomeEvent(
            user_id=user_oid,
            source_type="platform",
            source_name="swiggy",
            platform_type="food_delivery",
            amount=random.randint(2000, 3500),
            earned_at=today,
            description="Weekly payout",
        ))
    
    for event in events:
        await event.save()
    
    return {
        "success": True,
        "scenario": scenario,
        "events_created": len(events),
        "details": [
            {
                "type": "income" if isinstance(e, IncomeEvent) else "expense",
                "amount": e.amount,
                "description": e.description,
            }
            for e in events
        ]
    }


@router.delete("/reset")
async def reset_demo_data(
    current_user: User = Depends(get_current_user)
):
    """Clear all demo data for the current user and recreate default buckets."""
    from app.services.allocation import AllocationService
    
    user_oid = PydanticObjectId(str(current_user.id))
    await clear_user_data(user_oid)
    
    # Recreate default buckets so user can start fresh
    await AllocationService.create_default_buckets(str(current_user.id))
    
    return {
        "success": True,
        "message": "All financial data cleared. Default buckets created.",
    }
