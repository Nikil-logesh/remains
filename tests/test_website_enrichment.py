import httpx
import pytest

from app.models import CompanyIdentity
from app.website import WebsiteFetcher


def identity(name="Known Company AS"):
    return CompanyIdentity(
        organization_number="984851006", legal_name=name,
        address="Main Street 1", website="https://example.test/",
        source_url="https://registry.test/984851006",
        retrieved_at="2026-01-01T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_exact_identity_extracts_jsonld_and_open_graph():
    body = b"""<html><head><title>Known Company AS</title>
      <meta property="og:description" content="A useful description">
      <script type="application/ld+json">{"@type":"Organization","legalName":"Known Company AS","telephone":"+47123"}</script>
      </head><body>Known Company AS, Main Street 1</body></html>"""
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=body))) as client:
        result = await WebsiteFetcher(client, max_requests=1).enrich(identity())
    assert result["status"] == "available"
    assert result["pages"][0]["verified"]
    assert result["pages"][0]["fields"]["legalname"] == ["Known Company AS"]


@pytest.mark.asyncio
async def test_wrong_company_is_rejected():
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, content=b"<html>Different Company AS</html>")
    )) as client:
        result = await WebsiteFetcher(client, max_requests=1).enrich(identity())
    assert result["status"] == "ambiguous"
    assert result["reason"] == "website_identity_mismatch"


@pytest.mark.asyncio
async def test_source_failure_is_explicit_and_budgeted():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(503))) as client:
        result = await WebsiteFetcher(client, max_requests=2, retries=4).enrich(identity())
    assert result["status"] == "failed"
    assert result["requests"] == 2


@pytest.mark.asyncio
async def test_conflicting_metadata_is_preserved():
    def handler(request):
        title = "Known Company AS"
        description = "one" if request.url.path == "/" else "two"
        return httpx.Response(200, content=f'<title>{title}</title><meta name="description" content="{description}">Known Company AS'.encode())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await WebsiteFetcher(client, max_requests=2).enrich(identity())
    assert result["status"] == "available"
    assert "description" in result["conflicts"]
