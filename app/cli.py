"""Single-company CLI."""

import argparse
import asyncio
import json
from pathlib import Path

from app.clients.brreg import BrregClient
from app.config import get_settings
from app.storage.cache import RegistryCache
from app.batch import process_jsonl
from app.pipeline import build_profile
from app.profile import ProfileStore


async def lookup(organization_number: str, *, enrich: bool = False) -> dict:
    settings = get_settings()
    cache = RegistryCache(settings.cache_path)
    cached = cache.get(organization_number)
    if cached and not enrich:
        return cached.identity.model_dump(mode="json")
    async with BrregClient(
        settings.registry_base_url, settings.request_timeout_seconds
    ) as client:
        record = cached or await client.get_company(organization_number)
        cache.put(record)
        if enrich:
            envelope = await build_profile(organization_number, _CachedBrreg(record))
            return envelope.model_dump(mode="json")
    return record.identity.model_dump(mode="json")


class _CachedBrreg:
    def __init__(self, record):
        self.record = record

    async def get_company(self, _number):
        return self.record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("organization_number", nargs="?")
    parser.add_argument("--company", dest="company_number")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--input", "--batch-input", type=Path, help="JSONL batch input")
    parser.add_argument("--output", "--batch-output", type=Path, help="JSONL batch output (default: stdout)")
    parser.add_argument("--financial-dataset", type=Path, help="financial-filer JSONL snapshot")
    parser.add_argument("--run-id", help="stable batch run identifier")
    parser.add_argument("--enrich", action="store_true", help="verify and enrich from the registry website")
    args = parser.parse_args(argv)
    if args.input:
        dataset = args.financial_dataset or get_settings().financial_dataset_path
        with args.input.open("r", encoding="utf-8-sig") as source:
            if args.output:
                with args.output.open("w", encoding="utf-8") as target:
                    process_jsonl(source, target, financial_dataset=dataset, run_id=args.run_id,
                                  enrich=args.enrich, registry_base_url=get_settings().registry_base_url,
                                  request_timeout_seconds=get_settings().request_timeout_seconds)
            else:
                process_jsonl(source, __import__("sys").stdout, financial_dataset=dataset, run_id=args.run_id,
                              enrich=args.enrich, registry_base_url=get_settings().registry_base_url,
                              request_timeout_seconds=get_settings().request_timeout_seconds)
        return 0
    organization_number = args.company_number or args.organization_number
    if not organization_number:
        parser.error("provide an organization number or --company")
    try:
        result = asyncio.run(lookup(organization_number, enrich=args.enrich))
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["legal_name"])
    return 0
