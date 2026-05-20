import os
import requests
from dataclasses import dataclass
from typing import Optional

DEMO_BASE_URL = "https://demo-api-capital.backend.gbcdn.com/api/v1"
LIVE_BASE_URL = "https://api-capital.backend.gbcdn.com/api/v1"

# Tier 2 — standard setup, used 80% of the time per rules.json
RISK_PCT = 0.005  # 0.5% of account balance

# Instrument config: pip_size = price increment per pip, pip_value = USD per lot per pip
# Formula from rules.json: Risk Amount ÷ (stop_pips × pip_value) = Lot Size
# Verify Capital.com contract specs before going live — these are standard CFD defaults
INSTRUMENT_CONFIG: dict[str, dict] = {
    "GOLD":   {"epic": "GOLD",   "pip_size": 0.10,   "pip_value": 1.0},
    "XAUUSD": {"epic": "GOLD",   "pip_size": 0.10,   "pip_value": 1.0},
    "EURUSD": {"epic": "EURUSD", "pip_size": 0.0001, "pip_value": 10.0},
    "AUDUSD": {"epic": "AUDUSD", "pip_size": 0.0001, "pip_value": 10.0},
    "GBPUSD": {"epic": "GBPUSD", "pip_size": 0.0001, "pip_value": 10.0},
    "USDJPY": {"epic": "USDJPY", "pip_size": 0.01,   "pip_value": 9.09},
}


@dataclass
class TradeResult:
    success: bool
    deal_reference: Optional[str]
    size: Optional[float]
    direction: str
    epic: str
    message: str


class CapitalClient:
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

    def get_account_balance(self) -> float:
        resp = requests.get(
            f"{self.base_url}/accounts",
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        accounts = resp.json().get("accounts", [])
        for acc in accounts:
            if acc.get("preferred"):
                return float(acc["balance"]["balance"])
        return float(accounts[0]["balance"]["balance"])

    def _resolve_instrument(self, symbol: str) -> dict:
        cfg = INSTRUMENT_CONFIG.get(symbol.upper())
        if cfg:
            return cfg
        # Unknown instrument — default to standard forex pip specs
        return {"epic": symbol.upper(), "pip_size": 0.0001, "pip_value": 10.0}

    def _calculate_size(
        self,
        balance: float,
        entry_price: float,
        stop_price: float,
        pip_size: float,
        pip_value: float,
    ) -> float:
        risk_amount = balance * RISK_PCT
        stop_pips = abs(entry_price - stop_price) / pip_size
        if stop_pips == 0:
            return 0.01
        # rules.json formula: Risk Amount ÷ Stop Loss Distance (pips) = Lot Size
        # Lot Size = risk_amount / (stop_pips × pip_value_per_lot)
        size = risk_amount / (stop_pips * pip_value)
        return max(0.01, round(size, 2))

    def place_market_order(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_price: Optional[float] = None,
    ) -> TradeResult:
        direction_upper = direction.upper()
        if direction_upper not in ("BUY", "SELL"):
            return TradeResult(
                success=False,
                deal_reference=None,
                size=None,
                direction=direction,
                epic=symbol,
                message=f"Invalid direction: {direction}",
            )

        instrument = self._resolve_instrument(symbol)
        epic = instrument["epic"]

        try:
            self.authenticate()
            balance = self.get_account_balance()
            risk_amount = balance * RISK_PCT

            if stop_price is not None:
                size = self._calculate_size(
                    balance,
                    entry_price,
                    stop_price,
                    instrument["pip_size"],
                    instrument["pip_value"],
                )
            else:
                # No stop provided — use minimum size, do not risk real capital
                size = 0.01

            body: dict = {
                "direction": direction_upper,
                "epic": epic,
                "size": size,
                "guaranteedStop": False,
                "trailingStop": False,
            }
            if stop_price is not None:
                body["stopLevel"] = stop_price

            resp = requests.post(
                f"{self.base_url}/positions",
                headers=self._auth_headers(),
                json=body,
                timeout=10,
            )
            resp.raise_for_status()
            deal_ref = resp.json().get("dealReference", "unknown")

            return TradeResult(
                success=True,
                deal_reference=deal_ref,
                size=size,
                direction=direction_upper,
                epic=epic,
                message=(
                    f"{direction_upper} {size} lots {epic} | "
                    f"Risk: ${risk_amount:.0f} | Ref: {deal_ref}"
                ),
            )

        except Exception as exc:
            return TradeResult(
                success=False,
                deal_reference=None,
                size=None,
                direction=direction_upper,
                epic=epic,
                message=str(exc),
            )
