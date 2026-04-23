from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os

app = FastAPI()

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "Mathew-Trading-Alerts")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


class WebhookPayload(BaseModel):
    symbol: str
    action: str
    price: str
    timeframe: str | None = None


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload):
    message = f"{payload.action.upper()} {payload.symbol} @ {payload.price}"
    if payload.timeframe:
        message += f" ({payload.timeframe}m)"

    requests.post(
        NTFY_URL,
        data=message.encode("utf-8"),
        headers={
            "Title": f"TradingView Alert — {payload.symbol}",
            "Priority": "high",
        },
    )

    return {"status": "received", "message": message}
