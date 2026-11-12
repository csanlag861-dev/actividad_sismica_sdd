from __future__ import annotations

import sys

from observatorio.health import check_health


async def check_service(name: str) -> bool:
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
