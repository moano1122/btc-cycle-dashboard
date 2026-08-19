"""Configuración central. Todo se lee de .env con valores por defecto sensatos."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
FRONTEND_DIR = ROOT / "frontend"
DB_PATH = DATA_DIR / "cache.db"

DATA_DIR.mkdir(exist_ok=True)


def _int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    try:
        return int(raw)
    except ValueError:
        return default


# --- Fuente on-chain --------------------------------------------------------
BITCOIN_DATA_BASE = "https://api.bitcoin-data.com"
BITCOIN_DATA_API_KEY = (os.getenv("BITCOIN_DATA_API_KEY") or "").strip()
REQ_PER_HOUR = _int("BITCOIN_DATA_REQ_PER_HOUR", 10)
REQ_PER_DAY = _int("BITCOIN_DATA_REQ_PER_DAY", 15)

# --- Telegram ---------------------------------------------------------------
TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
TELEGRAM_CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# --- Servidor ---------------------------------------------------------------
HOST = os.getenv("HOST", "127.0.0.1")
PORT = _int("PORT", 8848)

# Cuántos días puede tener un dato antes de considerarse rancio. Las métricas
# on-chain se publican una vez al día, así que 3 días de margen absorbe fines
# de semana y retrasos del proveedor sin dar falsas alarmas.
STALE_AFTER_DAYS = 3
