import os
import sys
import requests
import uuid
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from capital_client import CapitalClient, TradeResult
except ImportError as e:
    print(f"Warning: Could not import CapitalClient: {e}")
    CapitalClient = None  # type: ignore
    TradeResult = None  # type: ignore

from auth import verify_api_key  # noqa: E402
from database import (  # noqa: E402
    insert_pending_trade,
    get_pending_trades,
    delete_pending_trade,
    delete_expired_pending_trades,
    insert_trade,
    Trade,
)

try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env: {e}")

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


class PendingTradeResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    entry_price: float
    stop_price: Optional[float]
    created_at: str
    expires_at: str


def send_ntfy_notification(message: str, title: str = "", priority: str = "default") -> dict:
    """Send notification to ntfy.sh and return result"""
    try:
        print(f"[NTFY] Sending to {NTFY_URL}")
        print(f"[NTFY] Title: {title}")
        print(f"[NTFY] Message: {message[:100]}...")

        response = requests.post(
            NTFY_URL,
            data=message.encode(),
            headers={"Title": title, "Priority": priority},
            timeout=5,
        )

        print(f"[NTFY] Status: {response.status_code}")
        print(f"[NTFY] Response: {response.text}")

        if response.status_code == 200:
            return {"success": True, "message": "Notification sent"}
        else:
            return {"success": False, "message": f"HTTP {response.status_code}"}

    except Exception as e:
        print(f"[NTFY] ERROR: {str(e)}")
        return {"success": False, "message": str(e)}


@app.get("/")
def health() -> dict:
    return {"status": "ok", "simulate": SIMULATE, "ntfy_topic": NTFY_TOPIC}


@app.post("/webhook", status_code=202)
async def receive_webhook(payload: WebhookPayload, api_key: str = Depends(verify_api_key)) -> dict:
    entry_price = float(payload.price)
    stop_price = float(payload.stop) if payload.stop else None
    trade_id = str(uuid.uuid4())
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

    insert_pending_trade(
        trade_id=trade_id,
        symbol=payload.symbol,
        direction=payload.action.upper(),
        entry_price=entry_price,
        stop_price=stop_price,
        expires_at=expires_at,
    )

    ntfy_body = (
        f"⏳ APPROVAL REQUIRED\n"
        f"{payload.action.upper()} {payload.symbol}\n"
        f"Entry: {entry_price:.2f}"
        + (f" | Stop: {stop_price:.2f}" if stop_price else "")
        + f"\nTrade ID: {trade_id}\n"
        f"Expires: {expires_at}\n"
        f"GET /pending to review or\n"
        f"GET /approve/{trade_id} to execute"
    )

    ntfy_result = send_ntfy_notification(
        message=ntfy_body,
        title=f"PENDING: {payload.action.upper()} {payload.symbol} @ {entry_price:.2f}",
        priority="high",
    )

    return {
        "status": "accepted",
        "trade_id": trade_id,
        "expires_at": expires_at,
        "message": "Trade queued for approval",
        "ntfy": ntfy_result,
    }


@app.get("/pending")
async def list_pending(api_key: str = Depends(verify_api_key)) -> dict:
    delete_expired_pending_trades()
    pending = get_pending_trades()
    return {
        "status": "ok",
        "count": len(pending),
        "trades": pending,
    }


async def execute_pending_trade(trade_id: str):
    """Execute a pending trade via Capital.com or simulation."""
    pending = get_pending_trades()
    trade_data = next((t for t in pending if t["id"] == trade_id), None)

    if not trade_data:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

    if SIMULATE:
        result = TradeResult(
            success=True,
            deal_reference=f"SIM-{trade_id[:8]}",
            size=1.0,
            direction=trade_data["direction"],
            epic=trade_data["symbol"],
            message=f"[SIMULATED] {trade_data['direction']} {trade_data['symbol']} "
                    f"@ {trade_data['entry_price']}",
        )
    else:
        if CapitalClient is None:
            raise HTTPException(status_code=500, detail="CapitalClient not available")
        client = CapitalClient()
        result = client.place_market_order(
            symbol=trade_data["symbol"],
            direction=trade_data["direction"].lower(),
            entry_price=trade_data["entry_price"],
            stop_price=trade_data["stop_price"],
        )

    return result


@app.get("/approve/{trade_id}")
async def approve_trade(trade_id: str, api_key: str = Depends(verify_api_key)) -> dict:
    try:
        result = await execute_pending_trade(trade_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    pending = get_pending_trades()
    trade_data = next((t for t in pending if t["id"] == trade_id), None)

    if not trade_data:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

    status = "FILLED" if result.success else "FAILED"
    sim_tag = "[SIM] " if SIMULATE else ""

    trade = Trade(
        id=trade_id,
        symbol=trade_data["symbol"],
        direction=trade_data["direction"],
        entry_price=trade_data["entry_price"],
        stop_price=trade_data["stop_price"],
        size=result.size,
        deal_reference=result.deal_reference,
        status=status,
        created_at=trade_data["created_at"],
        executed_at=datetime.utcnow().isoformat(),
        message=result.message,
    )

    insert_trade(trade)
    delete_pending_trade(trade_id)

    ntfy_body = (
        f"{sim_tag}{result.direction} {result.epic}\n"
        f"Entry: {trade_data['entry_price']:.2f}"
        + (f" | Stop: {trade_data['stop_price']:.2f}" if trade_data['stop_price'] else "")
        + f"\nSize: {result.size} lots\n"
        f"Ref: {result.deal_reference or 'N/A'}\n"
        f"{result.message}"
    )

    ntfy_result = send_ntfy_notification(
        message=ntfy_body,
        title=f"{sim_tag}{result.direction} {result.epic} - {status}",
        priority="high" if result.success else "urgent",
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)

    return {
        "status": "ok",
        "trade_id": trade_id,
        "result": result.message,
        "executed_at": trade.executed_at,
        "ntfy": ntfy_result,
    }
