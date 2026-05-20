import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


DB_PATH = os.path.join(os.path.dirname(__file__), "trading.db")


@dataclass
class Trade:
    id: str
    symbol: str
    direction: str
    entry_price: float
    stop_price: Optional[float]
    size: Optional[float]
    deal_reference: Optional[str]
    status: str  # pending, approved, filled, failed
    created_at: str
    executed_at: Optional[str]
    message: str


def init_db() -> None:
    """Initialize database with schema if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_price REAL,
            size REAL,
            deal_reference TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            executed_at TEXT,
            message TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_trades (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_price REAL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_trade(trade: Trade) -> None:
    """Insert a trade record into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO trades
        (id, symbol, direction, entry_price, stop_price, size,
         deal_reference, status, created_at, executed_at, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade.id,
        trade.symbol,
        trade.direction,
        trade.entry_price,
        trade.stop_price,
        trade.size,
        trade.deal_reference,
        trade.status,
        trade.created_at,
        trade.executed_at,
        trade.message,
    ))

    conn.commit()
    conn.close()


def update_trade(trade_id: str, **kwargs) -> None:
    """Update a trade record."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values()) + [trade_id]

    cursor.execute(f"UPDATE trades SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_trade(trade_id: str) -> Optional[Trade]:
    """Retrieve a single trade by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return Trade(
        id=row[0],
        symbol=row[1],
        direction=row[2],
        entry_price=row[3],
        stop_price=row[4],
        size=row[5],
        deal_reference=row[6],
        status=row[7],
        created_at=row[8],
        executed_at=row[9],
        message=row[10],
    )


def get_trades(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Trade]:
    """Retrieve trades with optional filters."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "SELECT * FROM trades WHERE 1=1"
    params: List[Any] = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    trades = []
    for row in rows:
        trades.append(Trade(
            id=row[0],
            symbol=row[1],
            direction=row[2],
            entry_price=row[3],
            stop_price=row[4],
            size=row[5],
            deal_reference=row[6],
            status=row[7],
            created_at=row[8],
            executed_at=row[9],
            message=row[10],
        ))

    return trades


def insert_pending_trade(
    trade_id: str,
    symbol: str,
    direction: str,
    entry_price: float,
    stop_price: Optional[float],
    expires_at: str
) -> None:
    """Insert a pending trade awaiting approval."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pending_trades
        (id, symbol, direction, entry_price, stop_price, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_id,
        symbol,
        direction,
        entry_price,
        stop_price,
        datetime.utcnow().isoformat(),
        expires_at,
    ))

    conn.commit()
    conn.close()


def get_pending_trades() -> List[Dict[str, Any]]:
    """Retrieve all pending trades awaiting approval."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, symbol, direction, entry_price, stop_price, created_at, expires_at
        FROM pending_trades
        ORDER BY created_at ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    pending = []
    for row in rows:
        pending.append({
            "id": row[0],
            "symbol": row[1],
            "direction": row[2],
            "entry_price": row[3],
            "stop_price": row[4],
            "created_at": row[5],
            "expires_at": row[6],
        })

    return pending


def delete_pending_trade(trade_id: str) -> None:
    """Remove a trade from pending queue."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pending_trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()


def delete_expired_pending_trades() -> None:
    """Remove all expired pending trades."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM pending_trades WHERE expires_at < ?",
        (datetime.utcnow().isoformat(),)
    )
    conn.commit()
    conn.close()


# Initialize database on module load
init_db()
