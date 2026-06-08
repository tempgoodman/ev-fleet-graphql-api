from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.dataloader import DataLoader

from app.models.energy_tariff import EnergyTariff


async def _load_energy_tariffs_by_ev_ids(
    ev_ids: list[UUID],
    session: AsyncSession,
) -> list[EnergyTariff | None]:
    if not ev_ids:
        return []

    result = await session.execute(
        select(EnergyTariff).where(EnergyTariff.ev_id.in_(ev_ids))
    )
    tariffs: Sequence[EnergyTariff] = result.scalars().all()
    tariff_by_ev_id = {tariff.ev_id: tariff for tariff in tariffs}
    return [tariff_by_ev_id.get(ev_id) for ev_id in ev_ids]


def create_energy_tariff_by_ev_id_loader(
    session: AsyncSession,
) -> DataLoader[UUID, EnergyTariff | None]:
    return DataLoader(
        load_fn=lambda ev_ids: _load_energy_tariffs_by_ev_ids(ev_ids, session)
    )
