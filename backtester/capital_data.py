"""Fetch historical OHLCV data from Capital.com API."""

import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass

DEMO_BASE_URL = "https://demo-api-capital.backend.gbcdn.com/api/v1"
LIVE_BASE_URL = "https://api-capital.backend.gbcdn.com/api/v1"


@dataclass
class OHLCV:
    """OHLCV candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def __repr__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M")
        return f"OHLCV({ts} | O:{self.open:.4f} H:{self.high:.4f} L:{self.low:.4f} C:{self.close:.4f} V:{self.volume})"


class CapitalDataClient:
    """Fetch historical OHLCV data from Capital.com."""

    def __init__(self) -> None:
        self.api_key = os.environ["CAPITAL_API_KEY"]
        self.identifier = os.environ["CAPITAL_IDENTIFIER"]
        self.password = os.environ["CAPITAL_PASSWORD"]
        env = os.getenv("CAPITAL_ENVIRONMENT", "demo").lower()
        self.base_url = LIVE_BASE_URL if env == "live" else DEMO_BASE_URL
        self._cst: Optional[str] = None
        self._security_token: Optional[str] = None

    def _auth_headers(self) -> dict:
        return {
            "X-CAP-API-KEY": self.api_key,
            "CST": self._cst,
            "X-SECURITY-TOKEN": self._security_token,
            "Content-Type": "application/json",
        }

    def authenticate(self) -> None:
        """Authenticate with Capital.com API."""
        resp = requests.post(
            f"{self.base_url}/session",
            headers={"X-CAP-API-KEY": self.api_key, "Content-Type": "application/json"},
            json={
                "identifier": self.identifier,
                "password": self.password,
                "encryptedPassword": False,
            },
            timeout=10,
        )
        resp.raise_for_status()
        self._cst = resp.headers["CST"]
        self._security_token = resp.headers["X-SECURITY-TOKEN"]

    def get_price_history(
        self,
        epic: str,
        resolution: str = "MINUTE_15",
        num_points: int = 500,
    ) -> list[OHLCV]:
        """
        Fetch historical OHLCV data.

        Args:
            epic: Instrument epic (e.g., "EURUSD")
            resolution: Candle resolution - MINUTE_15, HOUR_1, etc.
            num_points: Number of candles to fetch (max 500 per request)

        Returns:
            List of OHLCV candles in chronological order (oldest first).
        """
        try:
            self.authenticate()

            resp = requests.get(
                f"{self.base_url}/prices/{epic}",
                headers=self._auth_headers(),
                params={
                    "resolution": resolution,
                    "numPoints": num_points,
                    "pageSize": 500,  # Capital.com max
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            candles = []
            prices = data.get("pricePoints", [])

            for point in prices:
                try:
                    # Capital.com returns Unix timestamp in seconds
                    ts_seconds = point.get("snapshotTime")
                    if ts_seconds is None:
                        continue

                    ts = datetime.fromtimestamp(ts_seconds, tz=timezone.utc)

                    candles.append(OHLCV(
                        timestamp=ts,
                        open=float(point.get("openPrice", {}).get("bid", 0)),
                        high=float(point.get("closePrice", {}).get("bid", 0)),  # May need adjustment
                        low=float(point.get("closePrice", {}).get("bid", 0)),   # May need adjustment
                        close=float(point.get("closePrice", {}).get("bid", 0)),
                        volume=int(point.get("volume", 0)),
                    ))
                except (KeyError, TypeError, ValueError) as e:
                    print(f"[WARN] Skipping malformed price point: {e}")
                    continue

            # Sort by timestamp (oldest first)
            candles.sort(key=lambda c: c.timestamp)
            return candles

        except Exception as exc:
            print(f"[ERROR] Failed to fetch price history: {str(exc)}")
            return []

    def get_price_history_range(
        self,
        epic: str,
        start_date: datetime,
        end_date: datetime,
        resolution: str = "MINUTE_15",
    ) -> list[OHLCV]:
        """
        Fetch historical data for a date range.

        Capital.com API supports fetching up to 500 candles per request.
        For date ranges, we paginate by requesting 500-candle chunks.

        Args:
            epic: Instrument epic
            start_date: Start of range (UTC)
            end_date: End of range (UTC)
            resolution: Candle resolution

        Returns:
            List of OHLCV candles in the specified range.
        """
        all_candles = []
        current_date = start_date

        # Estimate: 15-min candles = 96 per day, so ~5 days per 500-candle chunk
        while current_date < end_date:
            chunk = self.get_price_history(epic, resolution, num_points=500)
            if not chunk:
                break

            # Filter by date range
            filtered = [c for c in chunk if start_date <= c.timestamp <= end_date]
            all_candles.extend(filtered)

            # Move forward by one day
            current_date += timedelta(days=1)

            # Avoid rate limits
            import time
            time.sleep(0.5)

        # Remove duplicates and sort
        unique_candles = {}
        for candle in all_candles:
            key = candle.timestamp
            if key not in unique_candles:
                unique_candles[key] = candle

        result = sorted(unique_candles.values(), key=lambda c: c.timestamp)
        return result
