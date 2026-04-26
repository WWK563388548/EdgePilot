import json
from datetime import date
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


class PolygonClientError(RuntimeError):
    pass


class PolygonClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _get_url(self, url: str) -> dict:
        if "apiKey=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode({'apiKey': self.api_key})}"

        try:
            with urlopen(url, timeout=30) as response:  # nosec B310 - trusted market data endpoint
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            raise PolygonClientError(f"Polygon HTTP error: {exc.code}") from exc
        except URLError as exc:
            raise PolygonClientError(f"Polygon request failed: {exc.reason}") from exc

        try:
            return json.loads(payload)
        except JSONDecodeError as exc:
            raise PolygonClientError("Polygon returned invalid JSON") from exc

    def _get(self, path: str, params: dict | None = None) -> dict:
        query = {"apiKey": self.api_key}
        if params:
            query.update(params)
        url = f"{self.base_url}{path}?{urlencode(query)}"
        return self._get_url(url)

    def list_daily_bars(self, ticker: str, from_date: date, to_date: date) -> list[dict]:
        payload = self._get(
            f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date.isoformat()}/{to_date.isoformat()}",
            params={"adjusted": "true", "sort": "asc", "limit": 5000},
        )
        return payload.get("results", [])

    def option_chain_snapshot(self, underlying_symbol: str, max_pages: int = 20) -> list[dict]:
        payload = self._get(
            f"/v3/snapshot/options/{underlying_symbol}",
            params={"limit": 250},
        )
        rows = list(payload.get("results", []))
        next_url = payload.get("next_url")
        pages = 1

        while next_url and pages < max_pages:
            payload = self._get_url(next_url)
            rows.extend(payload.get("results", []))
            next_url = payload.get("next_url")
            pages += 1

        if next_url:
            raise PolygonClientError("Polygon option chain pagination exceeded max_pages")

        return rows
