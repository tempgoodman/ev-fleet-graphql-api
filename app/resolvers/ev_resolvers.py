from __future__ import annotations

from uuid import UUID

import strawberry
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.events.event_hub import trigger_ev_status_publish
from app.models.ev import EV, EVStatus
from app.schemas.ev import CreateEVInput, UpdateEVInput


_GRAPHQL_TO_EV_COLUMN = {
    "id": EV.id,
    "make": EV.make,
    "model": EV.model,
    "batteryCapacityKwh": EV.battery_capacity_kwh,
    "battery_capacity_kwh": EV.battery_capacity_kwh,
    "rangeMiles": EV.range_miles,
    "range_miles": EV.range_miles,
    "monthlyLeasePrice": EV.monthly_lease_price,
    "monthly_lease_price": EV.monthly_lease_price,
    "status": EV.status,
    "createdAt": EV.created_at,
    "created_at": EV.created_at,
    "updatedAt": EV.updated_at,
    "updated_at": EV.updated_at,
}


def _collect_requested_ev_fields(
    selections: list[object],
    *,
    at_ev_level: bool = False,
) -> set[str]:
    requested_fields: set[str] = set()
    for selection in selections:
        selection_name = getattr(selection, "name", None)
        nested_selections = getattr(selection, "selections", None) or []

        if at_ev_level:
            if selection_name:
                requested_fields.add(selection_name)
                continue
            if nested_selections:
                requested_fields.update(
                    _collect_requested_ev_fields(nested_selections, at_ev_level=True),
                )
            continue

        if selection_name in {"ev", "evs"} and nested_selections:
            requested_fields.update(
                _collect_requested_ev_fields(nested_selections, at_ev_level=True),
            )
            continue

        if selection_name in _GRAPHQL_TO_EV_COLUMN:
            requested_fields.add(selection_name)
            continue

        if selection_name is None and nested_selections:
            requested_fields.update(_collect_requested_ev_fields(nested_selections))

    return requested_fields


def _ev_load_only_columns(
    info: strawberry.Info,
    make: str | None = None,
    max_price: float | None = None,
    status: str | None = None,
) -> list[object]:
    requested_fields = _collect_requested_ev_fields(info.selected_fields)
    selected_columns = {EV.id}
    if make is not None:
        selected_columns.add(EV.make)
    if max_price is not None:
        selected_columns.add(EV.monthly_lease_price)
    if status is not None:
        selected_columns.add(EV.status)
    for field_name in requested_fields:
        column = _GRAPHQL_TO_EV_COLUMN.get(field_name)
        if column is not None:
            selected_columns.add(column)
    return list(selected_columns)


def _apply_filters(
    query: Select[tuple[EV]],
    make: str | None,
    max_price: float | None,
    status: str | None,
) -> Select[tuple[EV]]:
    if make:
        query = query.where(EV.make.ilike(f"%{make}%"))

    if max_price is not None:
        query = query.where(EV.monthly_lease_price <= max_price)

    if status:
        normalized_status = status.upper()
        if normalized_status in EVStatus.__members__:
            query = query.where(EV.status == EVStatus[normalized_status])

    return query


async def get_ev(
    session: AsyncSession, info: strawberry.Info, ev_id: UUID
) -> EV | None:
    return await session.get(
        EV, ev_id, options=[load_only(*_ev_load_only_columns(info))]
    )


async def list_evs(
    session: AsyncSession,
    info: strawberry.Info,
    make: str | None = None,
    max_price: float | None = None,
    status: str | None = None,
) -> list[EV]:
    query = _apply_filters(
        select(EV).options(
            load_only(*_ev_load_only_columns(info, make, max_price, status))
        ),
        make,
        max_price,
        status,
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_ev(session: AsyncSession, input_data: CreateEVInput) -> EV:
    ev = EV(
        make=input_data.make,
        model=input_data.model,
        battery_capacity_kwh=input_data.battery_capacity_kwh,
        range_miles=input_data.range_miles,
        monthly_lease_price=input_data.monthly_lease_price,
        status=EVStatus(input_data.status.value),
    )
    session.add(ev)
    await session.commit()
    await session.refresh(ev)
    return ev


async def update_ev(
    session: AsyncSession, ev_id: UUID, input_data: UpdateEVInput
) -> EV | None:
    ev = await session.get(EV, ev_id)
    if not ev:
        return None

    old_status = ev.status.value

    if input_data.make is not None:
        ev.make = input_data.make
    if input_data.model is not None:
        ev.model = input_data.model
    if input_data.battery_capacity_kwh is not None:
        ev.battery_capacity_kwh = input_data.battery_capacity_kwh
    if input_data.range_miles is not None:
        ev.range_miles = input_data.range_miles
    if input_data.monthly_lease_price is not None:
        ev.monthly_lease_price = input_data.monthly_lease_price
    if input_data.status is not None:
        ev.status = EVStatus(input_data.status.value)

    await session.commit()
    await session.refresh(ev)

    if ev.status.value != old_status:
        await trigger_ev_status_publish(str(ev.id), ev.status.value)

    return ev


async def delete_ev(session: AsyncSession, ev_id: UUID) -> bool:
    ev = await session.get(EV, ev_id)
    if not ev:
        return False

    await session.delete(ev)
    await session.commit()
    return True
