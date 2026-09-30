"""Safe, bounded first-party website discovery and identity verification."""
from __future__ import annotations

import ipaddress
import json
import re
from collections import defaultdict
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.evidence import content_sha256, utc_now


class UrlRejected(ValueError):
    pass


def validate_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise UrlRejected("only authenticated http(s) URLs are allowed")
    host = parsed.hostname.lower().rstrip(".")
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
            raise UrlRejected("private or local hosts are not allowed")
    except ValueError:
        if host in {"localhost"} or "." not in host:
            raise UrlRejected("invalid public hostname")
    return parsed._replace(fragment="").geturl()


class WebsiteFetcher:
    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        max_bytes: int = 1_000_000,
        max_requests: int = 8,
        retries: int = 2,
        timeout: float = 10,
    ):
        self.client = client
        self.max_bytes = max_bytes
        self.max_requests = max(1, max_requests)
        self.retries = max(0, retries)
        self.timeout = timeout

    @staticmethod
    def normalize_website(value: str) -> str:
        """Return a canonical public origin/path, never adding credentials."""
        candidate = value.strip()
        if "://" not in candidate:
            candidate = "https://" + candidate
        safe = validate_url(candidate)
        parsed = urlparse(safe)
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return parsed._replace(scheme="https", path=path, query="", fragment="").geturl()

    @staticmethod
    def _norm(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

    @staticmethod
    def _extract(body: bytes) -> dict:
        soup = BeautifulSoup(body, "lxml")
        text = " ".join(soup.stripped_strings)
        values: dict[str, list[str]] = defaultdict(list)
        for tag in soup.find_all("meta"):
            key = tag.get("property") or tag.get("name")
            content = tag.get("content")
            if key and content and key.casefold() in {"og:title", "og:description", "description"}:
                values[key.casefold()].append(content.strip())
        for tag in soup.find_all("script", attrs={"type": re.compile("ld\\+json", re.I)}):
            try:
                data = json.loads(tag.string or tag.get_text())
            except (TypeError, ValueError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    for key in ("name", "legalName", "description", "url", "telephone", "email", "address"):
                        value = item.get(key)
                        if isinstance(value, dict):
                            value = ", ".join(str(v) for v in value.values() if v)
                        if isinstance(value, str) and value.strip():
                            values[key.casefold()].append(value.strip())
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        if title:
            values["title"].append(title)
        return {"text": text, "fields": dict(values)}

    async def fetch(self, url: str, expected_name: str | None = None) -> dict:
        safe = self.normalize_website(url)
        own = self.client is None
        client = self.client or httpx.AsyncClient(follow_redirects=False, timeout=self.timeout)
        try:
            response = await client.get(safe, headers={"Accept": "text/html,application/xhtml+xml"})
            if 300 <= response.status_code < 400:
                location = response.headers.get("location")
                if not location:
                    raise UrlRejected("redirect without location")
                target = validate_url(urljoin(safe, location))
                if urlparse(target).hostname != urlparse(safe).hostname:
                    raise UrlRejected("cross-domain redirect rejected")
                response = await client.get(target)
            response.raise_for_status()
            body = response.content
            if len(body) > self.max_bytes:
                raise UrlRejected("response exceeds size limit")
            extracted = self._extract(body)
            text = extracted["text"]
            legal = self._norm(expected_name) if expected_name else ""
            verified = not legal or legal in self._norm(text)
            return {"url": str(response.url), **extracted, "verified": verified,
                    "retrieved_at": utc_now(), "content_sha256": content_sha256(body)}
        finally:
            if own:
                await client.aclose()

    async def enrich(self, identity) -> dict:
        """Fetch only deterministic same-origin resources and return audit data."""
        if not identity.website:
            return {"status": "not_available", "reason": "registry_has_no_website", "pages": []}
        try:
            root = self.normalize_website(identity.website)
        except UrlRejected as exc:
            return {"status": "blocked", "reason": str(exc), "pages": []}
        parsed = urlparse(root)
        paths = [parsed.path or "/", "/about", "/contact", "/company", "/sitemap.xml", "/robots.txt"]
        urls = []
        for path in paths:
            candidate = urljoin(root, path)
            if urlparse(candidate).hostname == parsed.hostname and candidate not in urls:
                urls.append(candidate)
        own = self.client is None
        client = self.client or httpx.AsyncClient(follow_redirects=False, timeout=self.timeout)
        pages, errors, requests = [], [], 0
        try:
            for url in urls:
                if requests >= self.max_requests:
                    break
                for attempt in range(self.retries + 1):
                    if requests >= self.max_requests:
                        break
                    requests += 1
                    try:
                        page = await self.fetch(url, identity.legal_name) if client is self.client else await self._fetch_with_client(client, url, identity.legal_name)
                        pages.append(page)
                        break
                    except (httpx.HTTPError, UrlRejected, ValueError) as exc:
                        if attempt == self.retries:
                            errors.append({"url": url, "message": str(exc)})
        finally:
            if own:
                await client.aclose()
        def matches(page):
            haystack = self._norm(page["text"] + " " + " ".join(
                value for values in page.get("fields", {}).values() for value in values
            ))
            legal = self._norm(identity.legal_name)
            number = self._norm(identity.organization_number)
            address = self._norm(identity.address or "")
            return (legal and legal in haystack) or (number and number in haystack) or (address and address in haystack)
        for page in pages:
            page["verified"] = bool(matches(page))
        field_values = defaultdict(set)
        for page in pages:
            if page["verified"]:
                for field, values in page.get("fields", {}).items():
                    for value in values:
                        field_values[field].add(value)
        conflicts = {field: sorted(values) for field, values in field_values.items() if len(values) > 1}
        if not pages:
            return {"status": "failed", "reason": "no_public_pages", "pages": [], "errors": errors, "conflicts": {}, "requests": requests}
        verified = any(page["verified"] for page in pages)
        if not verified:
            return {"status": "ambiguous", "reason": "website_identity_mismatch", "pages": pages, "errors": errors, "conflicts": conflicts, "requests": requests}
        return {"status": "available", "pages": pages, "errors": errors, "conflicts": conflicts, "requests": requests}

    async def _fetch_with_client(self, client, url: str, expected_name: str | None) -> dict:
        original = self.client
        self.client = client
        try:
            return await self.fetch(url, expected_name)
        finally:
            self.client = original
