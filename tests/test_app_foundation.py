import httpx
import pytest

from app.clients.brreg import BrregClient
from app.models import CompanyIdentity
from app.validation.org_number import normalize_org_number, validate_org_number


def test_org_number_normalization_and_checksum():
    assert normalize_org_number("984 851 006") == "984851006"
    assert validate_org_number("984851006")
    assert not validate_org_number("984851007")
    assert not validate_org_number("123")


def test_company_identity_model():
    identity = CompanyIdentity(
        organization_number="984851006",
        legal_name="Test AS",
        source_url="https://example.test",
        retrieved_at="2026-01-01T00:00:00Z",
    )
    assert identity.legal_name == "Test AS"


@pytest.mark.asyncio
async def test_brreg_maps_official_payload():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/enheter/984851006")
        return httpx.Response(
            200,
            json={
                "organisasjonsnummer": "984851006",
                "navn": "Test AS",
                "organisasjonsform": {"beskrivelse": "Aksjeselskap"},
                "forretningsadresse": {
                    "adresse": ["Testgata 1"],
                    "postnummer": "0001",
                    "kommune": "Oslo",
                },
                "naeringskode1": {"kode": "62.010"},
                "hjemmeside": "https://example.test",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        brreg = BrregClient("https://example.test", client=client)
        record = await brreg.get_company("984851006")
    assert record.identity.legal_name == "Test AS"
    assert record.identity.address == "Testgata 1"
    assert record.identity.nace_code == "62.010"
