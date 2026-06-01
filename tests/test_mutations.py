from __future__ import annotations

import uuid

import pytest
from sqlalchemy import insert, select

from app.models.ev import EV, EVStatus


@pytest.mark.asyncio
async def test_create_ev_mutation(graphql_client):
    mutation = """
    mutation {
      createEv(
        input: {
          make: "Tesla"
          model: "Model 3"
          batteryCapacityKwh: 75
          rangeMiles: 333
          monthlyLeasePrice: 499.99
          status: AVAILABLE
        }
      ) {
        id
        make
        status
      }
    }
    """

    response = await graphql_client.post("/graphql", json={"query": mutation})
    payload = response.json()

    assert "errors" not in payload
    created = payload["data"]["createEv"]
    assert created["id"]
    assert created["make"] == "Tesla"
    assert created["status"] == "AVAILABLE"


@pytest.mark.asyncio
async def test_update_ev_supports_dynamic_field_selection(graphql_client, db_session):
    ev_id = uuid.uuid4()
    await db_session.execute(
        insert(EV),
        [
            {
                "id": ev_id,
                "make": "Nissan",
                "model": "Leaf",
                "battery_capacity_kwh": 62,
                "range_miles": 226,
                "monthly_lease_price": 289.99,
                "status": EVStatus.AVAILABLE,
            }
        ],
    )
    await db_session.commit()

    mutation = """
    mutation UpdateEV($id: UUID!) {
      updateEv(id: $id, input: { make: "Nissan+", status: LEASED }) {
        id
        make
        status
      }
    }
    """

    response = await graphql_client.post(
        "/graphql", json={"query": mutation, "variables": {"id": str(ev_id)}}
    )
    payload = response.json()

    assert "errors" not in payload
    updated = payload["data"]["updateEv"]
    assert updated["id"] == str(ev_id)
    assert updated["make"] == "Nissan+"
    assert updated["status"] == "LEASED"


@pytest.mark.asyncio
async def test_delete_ev_mutation(graphql_client, db_session):
    ev_id = uuid.uuid4()
    await db_session.execute(
        insert(EV),
        [
            {
                "id": ev_id,
                "make": "BMW",
                "model": "i4",
                "battery_capacity_kwh": 80,
                "range_miles": 300,
                "monthly_lease_price": 599.99,
                "status": EVStatus.AVAILABLE,
            }
        ],
    )
    await db_session.commit()

    mutation = """
    mutation DeleteEV($id: UUID!) {
      deleteEv(id: $id)
    }
    """

    response = await graphql_client.post(
        "/graphql", json={"query": mutation, "variables": {"id": str(ev_id)}}
    )
    payload = response.json()

    assert "errors" not in payload
    assert payload["data"]["deleteEv"] is True

    result = await db_session.execute(select(EV).where(EV.id == ev_id))
    assert result.scalar_one_or_none() is None
