from app.website import WebsiteFetcher


def test_registry_hostname_is_normalized_to_https():
    assert WebsiteFetcher.normalize_website("www.dnb.no") == "https://www.dnb.no/"
