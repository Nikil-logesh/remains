"""Bounded asynchronous profile pipeline."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from app.models import CompanyProfile, Evidence, Claim, OutputEnvelope
from app.profile import diff_profiles, validate_evidence
from app.website import WebsiteFetcher

async def build_profile(number: str, brreg, store=None, *, semaphore=None, website_fetcher=None) -> OutputEnvelope:
    sem = semaphore or asyncio.Semaphore(1)
    async with sem:
        previous = store.get(number) if store else None
        try:
            record = await brreg.get_company(number)
            identity = record.identity
            evidence = Evidence(id=f"registry-{number}", field="identity", status="available",
                source_type="official_registry", source_url=identity.source_url,
                retrieved_at=identity.retrieved_at, value=record.raw_response)
            profile = CompanyProfile(organization_number=identity.organization_number,
                legal_name=identity.legal_name, organization_form=identity.organization_form,
                website=identity.website, address=identity.address, postal_code=identity.postal_code,
                municipality=identity.municipality, employees=identity.employees,
                evidence=[evidence], retrieved_at=datetime.now(timezone.utc))
            profile.claims = [Claim(field="legal_name", value=identity.legal_name,
                                    confidence=1, evidence_ids=[evidence.id])]
            if identity.website:
                fetcher = website_fetcher or WebsiteFetcher()
                enrichment = await fetcher.enrich(identity)
                for index, page in enumerate(enrichment.get("pages", [])):
                    page_id = f"website-{number}-{index}"
                    profile.evidence.append(Evidence(
                        id=page_id, field="website", status="available" if page.get("verified") else "ambiguous",
                        source_type="first_party_website", source_url=page["url"],
                        retrieved_at=page["retrieved_at"], value=page.get("fields", {}),
                        content_sha256=page.get("content_sha256"),
                        note=None if page.get("verified") else "legal name was not found",
                    ))
                status = enrichment.get("status", "not_available")
                if status == "available":
                    verified = [e.id for e in profile.evidence if e.source_type == "first_party_website" and e.status == "available"]
                    profile.claims.append(Claim(field="website", value=identity.website,
                                                confidence=1.0, evidence_ids=verified))
                elif status in {"ambiguous", "failed", "blocked", "not_available"}:
                    profile.evidence.append(Evidence(
                        id=f"website-status-{number}", field="website", status=status,
                        source_type="first_party_website", source_url=identity.website,
                        retrieved_at=datetime.now(timezone.utc), note=enrichment.get("reason"),
                    ))
                    profile.claims.append(Claim(field="website", value=None, availability=status,
                                                confidence=1.0, evidence_ids=[f"website-status-{number}"]))
                for field, values in enrichment.get("conflicts", {}).items():
                    ids = [e.id for e in profile.evidence if e.source_type == "first_party_website" and e.status == "available"]
                    profile.claims.append(Claim(field=f"website.{field}", value=values,
                                                availability="ambiguous", confidence=0.0, evidence_ids=ids))
            validate_evidence(profile)
            if store: store.put(profile)
            return OutputEnvelope(organization_number=number, profile=profile,
                claims=profile.claims, evidence=profile.evidence, changes=diff_profiles(previous, profile))
        except Exception as exc:
            return OutputEnvelope(organization_number=number,
                profile=previous,
                claims=previous.claims if previous else [],
                evidence=previous.evidence if previous else [],
                errors=[{"code": "profile_failed", "availability": "failed", "message": str(exc)}])

async def batch_profiles(numbers, brreg, store=None, concurrency=4, website_fetcher=None):
    sem = asyncio.Semaphore(max(1, concurrency))
    return await asyncio.gather(*(build_profile(n, brreg, store, semaphore=sem, website_fetcher=website_fetcher) for n in numbers))
