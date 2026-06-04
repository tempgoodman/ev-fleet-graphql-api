from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

import strawberry

from app.models.energy_tariff import EnergyTariff


@strawberry.enum
class EVStatusType(enum.Enum):
    AVAILABLE = "AVAILABLE"
    LEASED = "LEASED"
    MAINTENANCE = "MAINTENANCE"


@strawberry.type
class EnergyTariffType:
    id: UUID
    name: str
    price_per_kwh: float
    ev_id: UUID


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

    @strawberry.field
    async def recommended_tariff(self, info: strawberry.Info) -> EnergyTariffType | None:
        loader = info.context["energy_tariff_by_ev_id_loader"]
        tariff: EnergyTariff | None = await loader.load(self.id)
        if tariff is None:
            return None

        return EnergyTariffType(
            id=tariff.id,
            name=tariff.name,
            price_per_kwh=tariff.price_per_kwh,
            ev_id=tariff.ev_id,
        )


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
