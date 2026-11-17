from __future__ import annotations

import sys

import httpx

from observatorio.health import check_health


async def check_service(name: str) -> bool:
    if (name or "").lower() == "api":
        try:
            async with httpx.AsyncClient(
                base_url="http://127.0.0.1:8000",
                timeout=5,
            ) as client:
                response = await client.get("/api/salud")
        except httpx.HTTPError:
            return False
        return response.status_code == 200
    return await check_health(name)


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "api"
    import asyncio

    ok = asyncio.run(check_service(name))
    if ok:
        print(f"{name}: healthy")
        raise SystemExit(0)
    print(f"{name}: unhealthy")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
