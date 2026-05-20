import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from capital_client import CapitalClient, TradeResult

load_dotenv()

app = FastAPI(title="TradingView Webhook → Capital.com")

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "Mathew-Trading-Alerts")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
SIMULATE = os.getenv("SIMULATE_TRADES", "true").lower() == "true"


class WebhookPayload(BaseModel):
    symbol: str
    action: str         # buy / sell
    price: str          # TradingView {{close}}
    timeframe: Optional[str] = None
    stop: Optional[str] = None  # stop-loss price level (optional but needed for correct sizing)


def send_ntfy_notification(message: str, title: str = "", priority: str = "default") -> None:
    try:
        requests.post(
            NTFY_URL,
            data=message.encode(),
            headers={"Title": title, "Priority": priority},
            timeout=5,
        )
    except Exception:
        pass


@app.get("/")
def health():
    return {"status": "ok", "simulate": SIMULATE, "ntfy_topic": NTFY_TOPIC}


@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload):
    entry_price = float(payload.price)
    stop_price = float(payload.stop) if payload.stop else None

    if SIMULATE:
        result = TradeResult(
            success=True,
            deal_reference="SIM-001",
            size=1.0,
            direction=payload.action.upper(),
            epic=payload.symbol,
            message=f"[SIMULATED] {payload.action.upper()} {payload.symbol} @ {entry_price}",
        )
    else:
        client = CapitalClient()
        result = client.place_market_order(
            symbol=payload.symbol,
            direction=payload.action,
            entry_price=entry_price,
            stop_price=stop_price,
        )

    status = "FILLED" if result.success else "FAILED"
    sim_tag = "[SIM] " if SIMULATE else ""

    ntfy_body = (
        f"{sim_tag}{result.direction} {result.epic}\n"
        f"Entry: {entry_price:.2f}"
        + (f" | Stop: {stop_price:.2f}" if stop_price else "")
        + f"\nSize: {result.size} lots\n"
        f"Ref: {result.deal_reference or 'N/A'}\n"
        f"{result.message}"
    )

    send_ntfy_notification(
        message=ntfy_body,
        title=f"{sim_tag}{payload.action.upper()} {payload.symbol} @ {entry_price:.2f} — {status}",
        priority="high" if result.success else "urgent",
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)

    return {"status": "ok", "simulate": SIMULATE, "result": result.message}
