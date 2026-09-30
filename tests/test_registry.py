import httpx
import pytest

from signalpost.registry import BrregClient, RegistryError


@pytest.mark.asyncio
async def test_registry_client_parses_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/enheter/984851006")
        return httpx.Response(200, json={"organisasjonsnummer": "984851006", "navn": "Test AS"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        organization = await BrregClient("https://example.test", client=http_client).get_organization("984851006")
    assert organization.name == "Test AS"


@pytest.mark.asyncio
async def test_registry_client_reports_not_found():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(404))) as client:
        with pytest.raises(RegistryError, match="not found"):
            await BrregClient("https://example.test", client=client).get_organization("984851006")
