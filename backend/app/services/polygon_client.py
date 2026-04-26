import json
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen


class PolygonClient:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict | None = None) -> dict:
        query = {"apiKey": self.api_key}
        if params:
            query.update(params)
        url = f"{self.base_url}{path}?{urlencode(query)}"
        with urlopen(url, timeout=30) as response:  # nosec B310 - trusted market data endpoint
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    def list_daily_bars(self, ticker: str, from_date: date, to_date: date) -> list[dict]:
        payload = self._get(
            f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date.isoformat()}/{to_date.isoformat()}",
            params={"adjusted": "true", "sort": "asc", "limit": 5000},
        )
        return payload.get("results", [])

    def option_chain_snapshot(self, underlying_symbol: str) -> list[dict]:
        payload = self._get(
            f"/v3/snapshot/options/{underlying_symbol}",
            params={"limit": 250},
        )
        return payload.get("results", [])
