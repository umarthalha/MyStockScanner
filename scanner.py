"""
scanner.py — fast pre-filter + batch OHLCV downloader

Pre-filter strategy (fast path):
  Download NSE's daily bhavcopy CSV — one HTTP request covers all ~2 100 EQ stocks.
  Filter: CLOSE_PRICE > 20  AND  TTL_TRD_QNTY > 50 000 (daily qty proxy for liquidity).
  Falls back to yfinance 1-month batches only if bhavcopy is unavailable.

Full OHLCV (batch_download):
  yf.download in groups of 50 with retry + back-off.
"""

import time
import requests
import yfinance as yf
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.5",
}

_RETRY_DELAY = 5.0
_MAX_RETRIES = 2
_BATCH_DELAY = 1.0   # seconds between yf.download batch calls


# ─── NSE bhavcopy pre-filter (primary — fast) ──────────────────────────────

def _bhavcopy_url(dt: datetime) -> str:
    return (
        "https://archives.nseindia.com/products/content/"
        f"sec_bhavdata_full_{dt.strftime('%d%m%Y')}.csv"
    )


def _fetch_bhavcopy() -> pd.DataFrame | None:
    """Try today and up to 5 previous calendar days (covers weekends/holidays)."""
    today = datetime.now()
    for offset in range(6):
        dt  = today - timedelta(days=offset)
        url = _bhavcopy_url(dt)
        try:
            r = requests.get(url, headers=_HEADERS, timeout=20)
            if r.status_code == 200 and len(r.text) > 1000:
                df = pd.read_csv(StringIO(r.text))
                df.columns = df.columns.str.strip()
                logger.info("Bhavcopy loaded: %s  (%d rows)", dt.strftime("%d-%m-%Y"), len(df))
                return df
        except Exception as e:
            logger.debug("Bhavcopy %s failed: %s", dt.strftime("%d%m%Y"), e)
    return None


def pre_filter_bhavcopy(stocks: list) -> list:
    """
    Pre-filter using NSE daily bhavcopy (one HTTP request).
    Keeps EQ stocks with CLOSE_PRICE > 20 and TTL_TRD_QNTY > 50 000.
    """
    df = _fetch_bhavcopy()
    if df is None:
        return []

    # Normalise column names — NSE sometimes has spaces
    # Expected cols: SYMBOL, SERIES, CLOSE_PRICE, TTL_TRD_QNTY
    req = {"SYMBOL", "SERIES"}
    if not req.issubset(set(df.columns)):
        logger.warning("Bhavcopy missing expected columns: %s", list(df.columns)[:10])
        return []

    # Identify price and volume columns (name varies slightly across NSE formats)
    price_col = next((c for c in df.columns if "CLOSE" in c), None)
    vol_col   = next((c for c in df.columns if "TRDQTY" in c or "TRD_QTY" in c
                      or "TRDQNTY" in c or "TRD_QNTY" in c or "QTY" in c), None)

    if not price_col or not vol_col:
        logger.warning("Bhavcopy: can't identify price/volume columns: %s", list(df.columns))
        return []

    df = df[df["SERIES"].str.strip() == "EQ"].copy()
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df[vol_col]   = pd.to_numeric(df[vol_col],   errors="coerce")
    df = df.dropna(subset=[price_col, vol_col])
    df = df[(df[price_col] > 20) & (df[vol_col] > 50_000)]

    passed_symbols = set(df["SYMBOL"].str.strip() + ".NS")

    filtered = [s for s in stocks if s["symbol"] in passed_symbols]
    logger.info("Bhavcopy pre-filter: %d / %d stocks passed (price>20, vol>50k)",
                len(filtered), len(stocks))
    return filtered


# ─── yfinance pre-filter fallback (slow path) ──────────────────────────────

def _download_with_retry(tickers, period, max_retries=_MAX_RETRIES):
    """yf.download with exponential back-off on rate-limit errors."""
    for attempt in range(max_retries + 1):
        try:
            return yf.download(
                tickers=tickers,
                period=period,
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                progress=False,
            )
        except Exception as e:
            msg = str(e)
            if "429" in msg or "Too Many Requests" in msg or "RateLimit" in msg:
                wait = _RETRY_DELAY * (2 ** attempt)
                logger.warning("Rate limited — sleeping %.0fs (retry %d/%d)",
                               wait, attempt + 1, max_retries)
                time.sleep(wait)
            else:
                raise
    return None


def _pre_filter_yf(stocks: list) -> list:
    """
    Fallback pre-filter via yfinance 1-month data in batches of 50.
    Slow but works if bhavcopy is unavailable.
    """
    symbols = [s["symbol"] for s in stocks]
    passed  = set()
    total   = len(symbols)

    for i in range(0, total, 50):
        batch = symbols[i:i + 50]
        logger.info("yf pre-filter batch %d-%d / %d …", i + 1, min(i + 50, total), total)
        try:
            raw = _download_with_retry(batch, "1mo")
            if raw is None:
                continue
            for sym in batch:
                try:
                    df = raw[sym].dropna() if len(batch) > 1 else raw.dropna()
                    if df.empty:
                        continue
                    price   = float(df["Close"].iloc[-1])
                    avg_vol = float(df["Volume"].mean())
                    if price > 20 and avg_vol > 200_000:
                        passed.add(sym)
                except Exception:
                    pass
        except Exception as e:
            logger.warning("yf pre-filter batch %d failed: %s", i, e)

        if i + 50 < total:
            time.sleep(_BATCH_DELAY)

    filtered = [s for s in stocks if s["symbol"] in passed]
    logger.info("yf pre-filter done: %d / %d passed", len(filtered), total)
    return filtered


# ─── Public pre_filter — tries bhavcopy first, yf fallback ─────────────────

def pre_filter(stocks: list) -> list:
    """
    Pre-filter stocks to liquid + priced candidates.
    Primary: NSE bhavcopy (~10 s for all 2 100+ stocks).
    Fallback: yfinance 1-month batches (slow, ~5 min).
    """
    result = pre_filter_bhavcopy(stocks)
    if result:
        return result
    logger.warning("Bhavcopy unavailable — falling back to yfinance pre-filter")
    return _pre_filter_yf(stocks)


# ─── batch_download — full OHLCV for filtered stocks ───────────────────────

def batch_download(symbols: list, period: str = "1y") -> dict:
    """
    Download OHLCV for a list of symbols using yf.download batch API.
    Returns {symbol: DataFrame} for symbols with >= 200 rows.
    """
    if not symbols:
        return {}
    raw = _download_with_retry(symbols, period)
    if raw is None:
        return {}
    result = {}
    for sym in symbols:
        try:
            df = raw[sym].dropna() if len(symbols) > 1 else raw.dropna()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            if "Close" not in df.columns or "Volume" not in df.columns:
                continue
            if len(df) >= 200:
                result[sym] = df
        except Exception:
            pass
    return result
