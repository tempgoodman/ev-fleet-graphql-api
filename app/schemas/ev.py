from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

import strawberry


@strawberry.enum
class EVStatusType(enum.Enum):
    AVAILABLE = "AVAILABLE"
    LEASED = "LEASED"
    MAINTENANCE = "MAINTENANCE"


@strawberry.type
class EVType:
    id: UUID
    make: str
    model: str
    battery_capacity_kwh: int
    range_miles: int
    monthly_lease_price: float
    status: EVStatusType
    created_at: datetime
    updated_at: datetime


@strawberry.input
class CreateEVInput:
    make: str
    model: str
    battery_capacity_kwh: int
    range_miles: int
    monthly_lease_price: float
    status: EVStatusType = EVStatusType.AVAILABLE


@strawberry.input
class UpdateEVInput:
    make: str | None = None
    model: str | None = None
    battery_capacity_kwh: int | None = None
    range_miles: int | None = None
    monthly_lease_price: float | None = None
    status: EVStatusType | None = None
