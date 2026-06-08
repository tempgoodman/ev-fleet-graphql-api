from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.energy_tariff import EnergyTariff


class EVStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    LEASED = "LEASED"
    MAINTENANCE = "MAINTENANCE"


class EV(Base):
    __tablename__ = "evs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    battery_capacity_kwh: Mapped[int] = mapped_column(Integer, nullable=False)
    range_miles: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_lease_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[EVStatus] = mapped_column(
        Enum(EVStatus, name="ev_status"), nullable=False, default=EVStatus.AVAILABLE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    recommended_tariff: Mapped[EnergyTariff | None] = relationship(
        back_populates="ev",
        uselist=False,
    )
