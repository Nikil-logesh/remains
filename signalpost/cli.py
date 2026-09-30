"""Single-company command-line flow."""

import argparse
import asyncio
import json
import logging

from .cache import SQLiteCache
from .config import get_settings
from .logging_config import configure_logging
from .registry import BrregClient, RegistryError

logger = logging.getLogger(__name__)


async def fetch_company(org_number: str) -> dict[str, object]:
    settings = get_settings()
    cache = SQLiteCache(settings.cache_path)
    client = BrregClient(settings.registry_base_url, settings.request_timeout_seconds)
    organization = await client.get_organization(org_number)
    cache.put(organization)
    return organization.model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Look up one Norwegian organization (read-only).")
    parser.add_argument("org_number", help="9-digit Norwegian organization number")
    parser.add_argument("--json", action="store_true", dest="as_json", help="print JSON")
    args = parser.parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    try:
        result = asyncio.run(fetch_company(args.org_number))
    except (RegistryError, ValueError) as exc:
        logger.error("%s", exc)
        return 2
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result.get('name')} ({result.get('org_number')})")
        if result.get("organization_form"):
            print(f"Form: {result['organization_form']}")
    return 0
