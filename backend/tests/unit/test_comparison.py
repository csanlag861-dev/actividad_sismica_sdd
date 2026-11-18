from __future__ import annotations

from datetime import datetime, timezone

import pytest

from observatorio.api.schemas import ApiError, parse_comparison_request


def valid_request() -> dict:
    return {
        "mode": "replay",
        "filters": {"min_mag": None},
        "groups": [
            {
                "id": "group-a",
                "label": "Primer grupo",
                "period": {
                    "start": "2025-01-01T01:00:00+01:00",
                    "end": "2025-01-02T00:00:00Z",
                },
                "population": {"type": "all"},
            },
            {
                "id": "group-b",
                "label": "Segundo grupo",
                "period": {
                    "start": "2025-01-02T00:00:00Z",
                    "end": "2025-01-03T00:00:00Z",
                },
                "population": {"type": "country", "country_id": "ESP"},
            },
        ],
    }


def test_comparison_request_normalizes_periods_and_preserves_groups() -> None:
    comparison = parse_comparison_request(valid_request())

    assert comparison.mode == "replay"
    assert comparison.min_mag is None
    assert comparison.groups[0].start == datetime(2025, 1, 1, tzinfo=timezone.utc)
    assert comparison.groups[0].end == datetime(2025, 1, 2, tzinfo=timezone.utc)
    assert comparison.groups[1].population.country_id == "ESP"


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (lambda body: body.update(mode=[]), "mode"),
        (lambda body: body.update(filters={"unknown": 1}), "filters"),
        (lambda body: body["groups"][1].update(id="group-a"), "groups[1].id"),
        (lambda body: body["groups"][1]["period"].update(start="2025-01-02T00:00:00"), "groups[1].period.start"),
        (lambda body: body["groups"][0]["population"].update(type=[]), "groups[0].population.type"),
        (lambda body: body["groups"][1]["population"].update(country_id="xxx"), "groups[1].population.country_id"),
        (lambda body: body.update(groups=[]), "groups"),
        (lambda body: body.update(extra="not allowed"), "body"),
    ],
)
def test_comparison_request_rejects_invalid_and_unknown_values(mutate, path: str) -> None:
    body = valid_request()
    mutate(body)

    with pytest.raises(ApiError) as error_info:
        parse_comparison_request(body)

    assert error_info.value.status_code == 422
    assert error_info.value.details[0]["parameter"] == path
