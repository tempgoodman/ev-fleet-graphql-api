from __future__ import annotations

import uuid

import pytest
from sqlalchemy import insert

from app.models.ev import EV, EVStatus


@pytest.mark.asyncio
async def test_evs_query_dynamic_filtering(graphql_client, db_session):
    await db_session.execute(
        insert(EV),
        [
            {
                "id": uuid.uuid4(),
                "make": "Tesla",
                "model": "Model 3",
                "battery_capacity_kwh": 75,
                "range_miles": 330,
                "monthly_lease_price": 499.99,
                "status": EVStatus.AVAILABLE,
            },
            {
                "id": uuid.uuid4(),
                "make": "Tesla",
                "model": "Model Y",
                "battery_capacity_kwh": 81,
                "range_miles": 310,
                "monthly_lease_price": 620.00,
                "status": EVStatus.AVAILABLE,
            },
            {
                "id": uuid.uuid4(),
                "make": "Nissan",
                "model": "Leaf",
                "battery_capacity_kwh": 62,
                "range_miles": 226,
                "monthly_lease_price": 299.00,
                "status": EVStatus.MAINTENANCE,
            },
        ],
    )
    await db_session.commit()

    query = """
    query {
      evs(make: "Tes", maxPrice: 550, status: "available") {
        make
        model
        monthlyLeasePrice
        status
      }
    }
    """

    response = await graphql_client.post("/graphql", json={"query": query})
    payload = response.json()

    assert "errors" not in payload
    items = payload["data"]["evs"]
    assert len(items) == 1
    assert items[0]["make"] == "Tesla"
    assert items[0]["model"] == "Model 3"
    assert items[0]["status"] == "AVAILABLE"


