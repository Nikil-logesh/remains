import pytest

from app.models import CompanyIdentity, RegistryRecord
from app.pipeline import build_profile
from app.profile import ProfileStore


class _Brreg:
    def __init__(self):
        self.fail = False

    async def get_company(self, number):
        if self.fail:
            raise RuntimeError("registry unavailable")
        identity = CompanyIdentity(
            organization_number=number,
            legal_name="Known Company AS",
            source_url="https://registry.example/" + number,
            retrieved_at="2026-01-01T00:00:00Z",
        )
        return RegistryRecord(identity=identity, raw_response={"navn": identity.legal_name})


@pytest.mark.asyncio
async def test_failed_refresh_keeps_prior_profile(tmp_path):
    store = ProfileStore(tmp_path / "profiles.sqlite")
    client = _Brreg()
    first = await build_profile("984851006", client, store)
    assert first.profile.legal_name == "Known Company AS"

    client.fail = True
    failed = await build_profile("984851006", client, store)
    assert failed.errors[0]["availability"] == "failed"
    assert failed.profile.legal_name == "Known Company AS"
    assert store.get("984851006").legal_name == "Known Company AS"
