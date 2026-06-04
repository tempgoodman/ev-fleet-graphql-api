from __future__ import annotations

import unittest

from app.resolvers.ev_resolvers import _ev_load_only_columns


class _Selection:
    def __init__(self, name: str | None = None, selections: list["_Selection"] | None = None) -> None:
        self.name = name
        self.selections = selections or []


class _Info:
    def __init__(self, selected_fields: list[_Selection]) -> None:
        self.selected_fields = selected_fields


class DynamicFieldSelectionTests(unittest.TestCase):
    def test_includes_primary_key_and_requested_direct_columns(self) -> None:
        info = _Info([_Selection("ev", [_Selection("make"), _Selection("monthlyLeasePrice")])])

        selected_columns = {column.key for column in _ev_load_only_columns(info)}

        self.assertSetEqual(selected_columns, {"id", "make", "monthly_lease_price"})

    def test_ignores_nested_relationship_fields(self) -> None:
        info = _Info(
            [
                _Selection(
                    "evs",
                    [
                        _Selection("recommendedTariff", [_Selection("status")]),
                        _Selection("model"),
                    ],
                )
            ],
        )

        selected_columns = {column.key for column in _ev_load_only_columns(info)}

        self.assertSetEqual(selected_columns, {"id", "model"})


if __name__ == "__main__":
    unittest.main()
