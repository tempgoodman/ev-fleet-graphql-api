from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import event

from app.models.ev import EV, EVStatus
from app.models.energy_tariff import EnergyTariff


@pytest.mark.asyncio
async def test_evs_query_applies_dynamic_filters(graphql_request, db_session) -> None:
    db_session.add_all(
        [
            EV(
                make="Tesla",
                model="Model 3",
                battery_capacity_kwh=75,
                range_miles=330,
                monthly_lease_price=499.99,
                status=EVStatus.AVAILABLE,
            ),
            EV(
                make="Tesla",
                model="Model X",
                battery_capacity_kwh=100,
                range_miles=340,
                monthly_lease_price=699.99,
                status=EVStatus.LEASED,
            ),
            EV(
                make="Ford",
                model="Mach-E",
                battery_capacity_kwh=70,
                range_miles=290,
                monthly_lease_price=539.99,
                status=EVStatus.AVAILABLE,
            ),
        ],
    )
    await db_session.commit()

    payload = await graphql_request(
        """
        query FilteredEvs($make: String, $maxPrice: Float, $status: String) {
          evs(make: $make, maxPrice: $maxPrice, status: $status) {
            id
            make
            model
            monthlyLeasePrice
            status
          }
        }
        """,
        {"make": "tes", "maxPrice": 550.0, "status": "available"},
    )

    assert "errors" not in payload
    assert payload["data"]["evs"] == [
        {
            "id": payload["data"]["evs"][0]["id"],
            "make": "Tesla",
            "model": "Model 3",
            "monthlyLeasePrice": 499.99,
            "status": "AVAILABLE",
        }
    ]


@pytest.mark.asyncio
async def test_recommended_tariff_is_batched_to_single_tariff_query(graphql_request, db_session) -> None:
    ev_one = EV(
        id=uuid4(),
        make="Tesla",
        model="Model 3",
        battery_capacity_kwh=75,
        range_miles=330,
        monthly_lease_price=499.99,
        status=EVStatus.AVAILABLE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    ev_two = EV(
        id=uuid4(),
        make="Nissan",
        model="Leaf",
        battery_capacity_kwh=62,
        range_miles=212,
        monthly_lease_price=329.99,
        status=EVStatus.AVAILABLE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add_all(
        [
            ev_one,
            ev_two,
            EnergyTariff(name="Saver", price_per_kwh=0.21, ev_id=ev_one.id),
            EnergyTariff(name="Night", price_per_kwh=0.18, ev_id=ev_two.id),
        ],
    )
    await db_session.commit()

    tariff_query_count: list[str] = []

    def _count_tariff_queries(_conn, _cursor, statement, _parameters, _context, _executemany) -> None:
        if "FROM energy_tariffs" in statement:
            tariff_query_count.append(statement)

    sync_engine = db_session.bind.sync_engine
    event.listen(sync_engine, "before_cursor_execute", _count_tariff_queries)
    try:
        payload = await graphql_request(
            """
            query {
              evs {
                id
                recommendedTariff {
                  name
                  pricePerKwh
                }
              }
            }
            """,
        )
    finally:
        event.remove(sync_engine, "before_cursor_execute", _count_tariff_queries)

    assert "errors" not in payload
    assert len(payload["data"]["evs"]) == 2
    assert len(tariff_query_count) == 1
