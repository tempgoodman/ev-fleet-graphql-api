from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.ev import EV, EVStatus


@pytest.mark.asyncio
async def test_create_ev_mutation_persists_record(graphql_request, db_session) -> None:
    payload = await graphql_request(
        """
        mutation CreateEv($input: CreateEVInput!) {
          createEv(input: $input) {
            id
            make
            model
            status
          }
        }
        """,
        {
            "input": {
                "make": "Tesla",
                "model": "Model Y",
                "batteryCapacityKwh": 75,
                "rangeMiles": 320,
                "monthlyLeasePrice": 529.99,
                "status": "AVAILABLE",
            }
        },
    )

    assert "errors" not in payload
    created = payload["data"]["createEv"]
    assert created["make"] == "Tesla"
    assert created["model"] == "Model Y"
    assert created["status"] == "AVAILABLE"

    result = await db_session.execute(select(EV).where(EV.id == UUID(created["id"])))
    assert result.scalar_one().model == "Model Y"


@pytest.mark.asyncio
async def test_update_ev_mutation_updates_record_with_minimal_selection(graphql_request, db_session) -> None:
    ev = EV(
        make="Nissan",
        model="Leaf",
        battery_capacity_kwh=62,
        range_miles=212,
        monthly_lease_price=329.99,
        status=EVStatus.AVAILABLE,
    )
    db_session.add(ev)
    await db_session.commit()
    await db_session.refresh(ev)

    payload = await graphql_request(
        """
        mutation UpdateEv($id: UUID!, $input: UpdateEVInput!) {
          updateEv(id: $id, input: $input) {
            id
          }
        }
        """,
        {
            "id": str(ev.id),
            "input": {
                "model": "Leaf Plus",
                "monthlyLeasePrice": 349.99,
                "status": "LEASED",
            },
        },
    )

    assert "errors" not in payload
    assert payload["data"]["updateEv"]["id"] == str(ev.id)

    await db_session.refresh(ev)
    assert ev.model == "Leaf Plus"
    assert ev.monthly_lease_price == 349.99
    assert ev.status == EVStatus.LEASED


@pytest.mark.asyncio
async def test_delete_ev_mutation_removes_record(graphql_request, db_session) -> None:
    ev = EV(
        make="Ford",
        model="Mach-E",
        battery_capacity_kwh=70,
        range_miles=290,
        monthly_lease_price=539.99,
        status=EVStatus.AVAILABLE,
    )
    db_session.add(ev)
    await db_session.commit()
    await db_session.refresh(ev)

    payload = await graphql_request(
        """
        mutation DeleteEv($id: UUID!) {
          deleteEv(id: $id)
        }
        """,
        {"id": str(ev.id)},
    )

    assert "errors" not in payload
    assert payload["data"]["deleteEv"] is True
    assert await db_session.get(EV, ev.id) is None
