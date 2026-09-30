from signalpost.cache import SQLiteCache
from signalpost.models import Organization


def test_cache_round_trip(tmp_path):
    cache = SQLiteCache(tmp_path / "cache.sqlite3")
    organization = Organization.model_validate({"organisasjonsnummer": "984851006", "navn": "Test AS"})
    cache.put(organization)
    cached = cache.get("984851006")
    assert cached is not None
    assert cached.organization.name == "Test AS"
