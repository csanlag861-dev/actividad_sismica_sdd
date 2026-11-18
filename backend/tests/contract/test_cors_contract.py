from __future__ import annotations

import pytest

from observatorio.api.app import create_app
from observatorio.config import parse_cors_origins


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "http://published.example",
        "https://user:pass@published.example",
        "https://published.example/path",
        "https://published.example,not-an-origin",
    ],
)
def test_invalid_production_cors_origin_configuration_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        parse_cors_origins(value)


def test_empty_production_origin_list_allows_only_development() -> None:
    assert parse_cors_origins("") == ["http://localhost:4200"]


@pytest.mark.asyncio
async def test_cors_preflight_and_get_allow_production_and_development_origins(api_context) -> None:
    client, _, _ = api_context

    for origin in ("https://frontend.example", "http://localhost:4200"):
        preflight = await client.options(
            "/api/eventos",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "ngrok-skip-browser-warning",
            },
        )
        post_preflight = await client.options(
            "/api/comparaciones",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        get_response = await client.get("/api/eventos", headers={"Origin": origin})

        assert preflight.status_code == 200
        assert post_preflight.status_code == 200
        assert "POST" in post_preflight.headers["access-control-allow-methods"]
        assert "content-type" in post_preflight.headers["access-control-allow-headers"]
        assert preflight.headers["access-control-allow-origin"] == origin
        assert "ngrok-skip-browser-warning" in preflight.headers["access-control-allow-headers"]
        assert get_response.status_code == 200
        assert get_response.headers["access-control-allow-origin"] == origin

    denied = await client.options(
        "/api/eventos",
        headers={
            "Origin": "https://unknown.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in denied.headers
