from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.ev import EV


class EnergyTariff(Base):
    __tablename__ = "energy_tariffs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_per_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    ev_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    ev: Mapped[EV] = relationship(back_populates="recommended_tariff")
