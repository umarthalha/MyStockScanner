"""
AI Khan — Complete Single-File Backend v3.0 (FINAL)
Run: pip install fastapi uvicorn yfinance pandas numpy && python main.py
"""

import logging
import time
import threading
import numpy as np
import pandas as pd
import yfinance as yf
try:
    import feedparser
except ImportError:
    feedparser = None

from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from universe import fetch_all_nse_stocks
from scanner import pre_filter, batch_download
from alerts import send_alerts, send_telegram_test, send_email_test

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ai_khan")

# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSE — NSE + BSE combined (~165 stocks)
# ─────────────────────────────────────────────────────────────────────────────

NIFTY200_STOCKS = [
    {"symbol": "RELIANCE.NS",   "name": "Reliance Industries",         "sector": "Energy"},
    {"symbol": "TCS.NS",        "name": "Tata Consultancy Services",   "sector": "IT"},
    {"symbol": "HDFCBANK.NS",   "name": "HDFC Bank",                   "sector": "Banking"},
    {"symbol": "INFY.NS",       "name": "Infosys",                     "sector": "IT"},
    {"symbol": "ICICIBANK.NS",  "name": "ICICI Bank",                  "sector": "Banking"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever",          "sector": "FMCG"},
    {"symbol": "ITC.NS",        "name": "ITC Ltd",                     "sector": "FMCG"},
    {"symbol": "SBIN.NS",       "name": "State Bank of India",         "sector": "Banking"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance",               "sector": "NBFC"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel",               "sector": "Telecom"},
    {"symbol": "KOTAKBANK.NS",  "name": "Kotak Mahindra Bank",         "sector": "Banking"},
    {"symbol": "LT.NS",         "name": "Larsen & Toubro",             "sector": "Capital Goods"},
    {"symbol": "HCLTECH.NS",    "name": "HCL Technologies",            "sector": "IT"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints",                "sector": "Paints"},
    {"symbol": "AXISBANK.NS",   "name": "Axis Bank",                   "sector": "Banking"},
    {"symbol": "MARUTI.NS",     "name": "Maruti Suzuki",               "sector": "Auto"},
    {"symbol": "SUNPHARMA.NS",  "name": "Sun Pharmaceuticals",         "sector": "Pharma"},
    {"symbol": "TITAN.NS",      "name": "Titan Company",               "sector": "Consumer"},
    {"symbol": "WIPRO.NS",      "name": "Wipro",                       "sector": "IT"},
    {"symbol": "ONGC.NS",       "name": "ONGC",                        "sector": "Oil & Gas"},
    {"symbol": "NTPC.NS",       "name": "NTPC",                        "sector": "Power"},
    {"symbol": "POWERGRID.NS",  "name": "Power Grid Corp",             "sector": "Power"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement",            "sector": "Cement"},
    {"symbol": "NESTLEIND.NS",  "name": "Nestle India",                "sector": "FMCG"},
    {"symbol": "MM.NS",         "name": "Mahindra & Mahindra",         "sector": "Auto"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors",                 "sector": "Auto"},
    {"symbol": "TATASTEEL.NS",  "name": "Tata Steel",                  "sector": "Metal"},
    {"symbol": "HINDALCO.NS",   "name": "Hindalco Industries",         "sector": "Metal"},
    {"symbol": "JSWSTEEL.NS",   "name": "JSW Steel",                   "sector": "Metal"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports",                 "sector": "Infrastructure"},
    {"symbol": "COALINDIA.NS",  "name": "Coal India",                  "sector": "Mining"},
    {"symbol": "TECHM.NS",      "name": "Tech Mahindra",               "sector": "IT"},
    {"symbol": "DRREDDY.NS",    "name": "Dr. Reddy's Laboratories",    "sector": "Pharma"},
    {"symbol": "DIVISLAB.NS",   "name": "Divi's Laboratories",         "sector": "Pharma"},
    {"symbol": "CIPLA.NS",      "name": "Cipla",                       "sector": "Pharma"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals",            "sector": "Healthcare"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv",               "sector": "NBFC"},
    {"symbol": "GRASIM.NS",     "name": "Grasim Industries",           "sector": "Cement"},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank",               "sector": "Banking"},
    {"symbol": "EICHERMOT.NS",  "name": "Eicher Motors",               "sector": "Auto"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp",               "sector": "Auto"},
    {"symbol": "BRITANNIA.NS",  "name": "Britannia Industries",        "sector": "FMCG"},
    {"symbol": "BPCL.NS",       "name": "BPCL",                        "sector": "Oil & Gas"},
    {"symbol": "SHREECEM.NS",   "name": "Shree Cement",                "sector": "Cement"},
    {"symbol": "BAJAJAUTO.NS",  "name": "Bajaj Auto",                  "sector": "Auto"},
    {"symbol": "PIDILITIND.NS", "name": "Pidilite Industries",         "sector": "Chemicals"},
    {"symbol": "HAVELLS.NS",    "name": "Havells India",               "sector": "Consumer Electric"},
    {"symbol": "MUTHOOTFIN.NS", "name": "Muthoot Finance",             "sector": "NBFC"},
    {"symbol": "GODREJCP.NS",   "name": "Godrej Consumer Products",    "sector": "FMCG"},
    {"symbol": "DABUR.NS",      "name": "Dabur India",                 "sector": "FMCG"},
    {"symbol": "MARICO.NS",     "name": "Marico",                      "sector": "FMCG"},
    {"symbol": "COLPAL.NS",     "name": "Colgate-Palmolive",           "sector": "FMCG"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products",      "sector": "FMCG"},
    {"symbol": "ICICIGI.NS",    "name": "ICICI General Insurance",     "sector": "Insurance"},
    {"symbol": "ICICIPRULI.NS", "name": "ICICI Prudential Life",       "sector": "Insurance"},
    {"symbol": "SBILIFE.NS",    "name": "SBI Life Insurance",          "sector": "Insurance"},
    {"symbol": "HDFCLIFE.NS",   "name": "HDFC Life Insurance",         "sector": "Insurance"},
    {"symbol": "AMBUJACEM.NS",  "name": "Ambuja Cements",              "sector": "Cement"},
    {"symbol": "ACC.NS",        "name": "ACC Limited",                 "sector": "Cement"},
    {"symbol": "VEDL.NS",       "name": "Vedanta",                     "sector": "Metal"},
    {"symbol": "HINDZINC.NS",   "name": "Hindustan Zinc",              "sector": "Metal"},
    {"symbol": "NMDC.NS",       "name": "NMDC",                        "sector": "Mining"},
    {"symbol": "SAIL.NS",       "name": "Steel Authority of India",    "sector": "Metal"},
    {"symbol": "TATAPOWER.NS",  "name": "Tata Power",                  "sector": "Power"},
    {"symbol": "ADANIGREEN.NS", "name": "Adani Green Energy",          "sector": "Renewable Energy"},
    {"symbol": "CANBK.NS",      "name": "Canara Bank",                 "sector": "Banking"},
    {"symbol": "BANKBARODA.NS", "name": "Bank of Baroda",              "sector": "Banking"},
    {"symbol": "PNB.NS",        "name": "Punjab National Bank",        "sector": "Banking"},
    {"symbol": "FEDERALBNK.NS", "name": "Federal Bank",                "sector": "Banking"},
    {"symbol": "IDFCFIRSTB.NS", "name": "IDFC First Bank",             "sector": "Banking"},
    {"symbol": "BANDHANBNK.NS", "name": "Bandhan Bank",                "sector": "Banking"},
    {"symbol": "AUROPHARMA.NS", "name": "Aurobindo Pharma",            "sector": "Pharma"},
    {"symbol": "TORNTPHARM.NS", "name": "Torrent Pharmaceuticals",     "sector": "Pharma"},
    {"symbol": "BIOCON.NS",     "name": "Biocon",                      "sector": "Pharma"},
    {"symbol": "LUPIN.NS",      "name": "Lupin",                       "sector": "Pharma"},
    {"symbol": "ALKEM.NS",      "name": "Alkem Laboratories",          "sector": "Pharma"},
    {"symbol": "JUBLFOOD.NS",   "name": "Jubilant Foodworks",          "sector": "Retail"},
    {"symbol": "DMART.NS",      "name": "Avenue Supermarts (DMart)",   "sector": "Retail"},
    {"symbol": "TRENT.NS",      "name": "Trent",                       "sector": "Retail"},
    {"symbol": "MPHASIS.NS",    "name": "Mphasis",                     "sector": "IT"},
    {"symbol": "LTIM.NS",       "name": "LTIMindtree",                 "sector": "IT"},
    {"symbol": "PERSISTENT.NS", "name": "Persistent Systems",          "sector": "IT"},
    {"symbol": "COFORGE.NS",    "name": "Coforge",                     "sector": "IT"},
    {"symbol": "OFSS.NS",       "name": "Oracle Financial Services",   "sector": "IT"},
    {"symbol": "KPIT.NS",       "name": "KPIT Technologies",           "sector": "IT"},
    {"symbol": "NYKAA.NS",      "name": "Nykaa",                       "sector": "Internet"},
    {"symbol": "PAYTM.NS",      "name": "Paytm",                       "sector": "Fintech"},
    {"symbol": "IRCTC.NS",      "name": "IRCTC",                       "sector": "Travel"},
    {"symbol": "LICI.NS",       "name": "LIC India",                   "sector": "Insurance"},
    {"symbol": "NHPC.NS",       "name": "NHPC",                        "sector": "Power"},
    {"symbol": "RECLTD.NS",     "name": "REC Limited",                 "sector": "Finance"},
    {"symbol": "PFC.NS",        "name": "Power Finance Corp",          "sector": "Finance"},
    {"symbol": "IRFC.NS",       "name": "Indian Railway Finance Corp", "sector": "Finance"},
    {"symbol": "ZOMATO.NS",     "name": "Zomato",                      "sector": "Internet"},
    {"symbol": "POLICYBZR.NS",  "name": "PB Fintech (PolicyBazaar)",   "sector": "Internet"},
    {"symbol": "ADANIENT.NS",   "name": "Adani Enterprises",           "sector": "Conglomerate"},
    {"symbol": "SIEMENS.NS",    "name": "Siemens India",               "sector": "Capital Goods"},
    {"symbol": "ABB.NS",        "name": "ABB India",                   "sector": "Capital Goods"},
    {"symbol": "BOSCHLTD.NS",   "name": "Bosch Ltd",                   "sector": "Auto Ancillary"},
    {"symbol": "DIXON.NS",      "name": "Dixon Technologies",          "sector": "Electronics"},
    {"symbol": "VOLTAS.NS",     "name": "Voltas",                      "sector": "Consumer Electric"},
]

BSE_ADDITIONS = [
    {"symbol": "ADANIPOWER.BO",  "name": "Adani Power",        "sector": "Power"},
    {"symbol": "CESC.BO",        "name": "CESC Limited",       "sector": "Power"},
    {"symbol": "CONCOR.BO",      "name": "Container Corp",     "sector": "Logistics"},
    {"symbol": "DLF.BO",         "name": "DLF Limited",        "sector": "Real Estate"},
    {"symbol": "GODREJPROP.BO",  "name": "Godrej Properties",  "sector": "Real Estate"},
    {"symbol": "HDFCAMC.BO",     "name": "HDFC AMC",           "sector": "Finance"},
    {"symbol": "IOC.BO",         "name": "Indian Oil Corp",    "sector": "Oil & Gas"},
    {"symbol": "JSWENERGY.BO",   "name": "JSW Energy",         "sector": "Power"},
    {"symbol": "KALYANKJIL.BO",  "name": "Kalyan Jewellers",   "sector": "Retail"},
    {"symbol": "LALPATHLAB.BO",  "name": "Dr Lal PathLabs",    "sector": "Healthcare"},
    {"symbol": "MAZDOCK.BO",     "name": "Mazagon Dock",       "sector": "Defence"},
    {"symbol": "MRF.BO",         "name": "MRF",                "sector": "Auto Ancillary"},
    {"symbol": "NAUKRI.BO",      "name": "Info Edge (Naukri)", "sector": "Internet"},
    {"symbol": "OBEROIRLTY.BO",  "name": "Oberoi Realty",      "sector": "Real Estate"},
    {"symbol": "PAGEIND.BO",     "name": "Page Industries",    "sector": "Apparel"},
    {"symbol": "SBICARD.BO",     "name": "SBI Cards",          "sector": "Finance"},
    {"symbol": "SJVN.BO",        "name": "SJVN Limited",       "sector": "Power"},
    {"symbol": "SUZLON.BO",      "name": "Suzlon Energy",      "sector": "Renewable Energy"},
    {"symbol": "TORNTPOWER.BO",  "name": "Torrent Power",      "sector": "Power"},
    {"symbol": "UNIONBANK.BO",   "name": "Union Bank",         "sector": "Banking"},
    {"symbol": "VARUNBEV.BO",    "name": "Varun Beverages",    "sector": "Beverages"},
    {"symbol": "ZEEL.BO",        "name": "Zee Entertainment",  "sector": "Media"},
    {"symbol": "SUPREMEIND.BO",  "name": "Supreme Industries", "sector": "Plastics"},
    {"symbol": "IREDA.BO",       "name": "IREDA",              "sector": "Finance"},
    {"symbol": "INOXWIND.BO",    "name": "Inox Wind",          "sector": "Renewable Energy"},
    {"symbol": "INDIANB.BO",     "name": "Indian Bank",        "sector": "Banking"},
]

NSE_MIDCAP_ADDITIONS = [
    {"symbol": "ANGELONE.NS",    "name": "Angel One",             "sector": "Finance"},
    {"symbol": "ASTRAL.NS",      "name": "Astral Ltd",            "sector": "Plastics"},
    {"symbol": "BLUESTARCO.NS",  "name": "Blue Star",             "sector": "Consumer Electric"},
    {"symbol": "CANFINHOME.NS",  "name": "Can Fin Homes",         "sector": "Housing Finance"},
    {"symbol": "CROMPTON.NS",    "name": "Crompton Greaves",      "sector": "Consumer Electric"},
    {"symbol": "DELHIVERY.NS",   "name": "Delhivery",             "sector": "Logistics"},
    {"symbol": "EMAMILTD.NS",    "name": "Emami Ltd",             "sector": "FMCG"},
    {"symbol": "FINEORG.NS",     "name": "Fine Organic",          "sector": "Chemicals"},
    {"symbol": "GLAND.NS",       "name": "Gland Pharma",          "sector": "Pharma"},
    {"symbol": "HAPPSTMNDS.NS",  "name": "Happiest Minds",        "sector": "IT"},
    {"symbol": "INDHOTEL.NS",    "name": "Indian Hotels (Taj)",   "sector": "Hospitality"},
    {"symbol": "KAYNES.NS",      "name": "Kaynes Technology",     "sector": "Electronics"},
    {"symbol": "KFINTECH.NS",    "name": "KFin Technologies",     "sector": "Finance"},
    {"symbol": "LAURUSLABS.NS",  "name": "Laurus Labs",           "sector": "Pharma"},
    {"symbol": "MASTEK.NS",      "name": "Mastek",                "sector": "IT"},
    {"symbol": "MAXHEALTH.NS",   "name": "Max Healthcare",        "sector": "Healthcare"},
    {"symbol": "METROPOLIS.NS",  "name": "Metropolis Healthcare", "sector": "Healthcare"},
    {"symbol": "NAVINFLUOR.NS",  "name": "Navin Fluorine",        "sector": "Chemicals"},
    {"symbol": "RITES.NS",       "name": "RITES Ltd",             "sector": "Infrastructure"},
    {"symbol": "SOLARINDS.NS",   "name": "Solar Industries",      "sector": "Defence"},
    {"symbol": "SONACOMS.NS",    "name": "Sona BLW Precision",    "sector": "Auto Ancillary"},
    {"symbol": "STAR.NS",        "name": "Star Health Insurance", "sector": "Insurance"},
    {"symbol": "TATACHEM.NS",    "name": "Tata Chemicals",        "sector": "Chemicals"},
    {"symbol": "TATACOMM.NS",    "name": "Tata Communications",   "sector": "Telecom"},
    {"symbol": "TATAELXSI.NS",   "name": "Tata Elxsi",            "sector": "IT"},
    {"symbol": "TRIDENT.NS",     "name": "Trident Ltd",           "sector": "Textiles"},
    {"symbol": "VGUARD.NS",      "name": "V-Guard Industries",    "sector": "Consumer Electric"},
    {"symbol": "WELCORP.NS",     "name": "Welspun Corp",          "sector": "Metal"},
    {"symbol": "ZENTEC.NS",      "name": "Zen Technologies",      "sector": "Defence"},
    {"symbol": "BIKAJI.NS",      "name": "Bikaji Foods",          "sector": "FMCG"},
    {"symbol": "CLEAN.NS",       "name": "Clean Science Tech",    "sector": "Chemicals"},
    {"symbol": "CONCORDBIO.NS",  "name": "Concord Biotech",       "sector": "Pharma"},
    {"symbol": "JKTYRE.NS",      "name": "JK Tyre",               "sector": "Auto Ancillary"},
    {"symbol": "KANSAINER.NS",   "name": "Kansai Nerolac",        "sector": "Paints"},
    {"symbol": "ROUTE.NS",       "name": "Route Mobile",          "sector": "IT"},
    {"symbol": "SWSOLAR.NS",     "name": "Sterling Wilson Solar", "sector": "Renewable Energy"},
    {"symbol": "TIMKEN.NS",      "name": "Timken India",          "sector": "Industrial"},
    {"symbol": "NETWORK18.NS",   "name": "Network18",             "sector": "Media"},
    {"symbol": "CRISIL.NS",      "name": "CRISIL",                "sector": "Finance"},
    {"symbol": "ELECON.NS",      "name": "Elecon Engineering",    "sector": "Capital Goods"},
]

ALL_STOCKS = NIFTY200_STOCKS + NSE_MIDCAP_ADDITIONS + BSE_ADDITIONS


# ─────────────────────────────────────────────────────────────────────────────
# TECHNICAL INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast    = close.ewm(span=fast,   adjust=False).mean()
    ema_slow    = close.ewm(span=slow,   adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high  = df["High"]
    low   = df["Low"]
    close = df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    avg = volume.rolling(period).mean()
    return volume / avg.replace(0, np.nan)

def support_resistance(df: pd.DataFrame, lookback: int = 5):
    recent     = df.tail(lookback * 5)
    support    = float(recent["Low"].min())
    resistance = float(recent["High"].max())
    return support, resistance

def bullish_rsi_divergence(close: pd.Series, rsi_s: pd.Series, lookback: int = 25) -> bool:
    try:
        c = close.iloc[-lookback:]
        r = rsi_s.iloc[-lookback:]
        price_low_now  = c.iloc[-1] < c.iloc[:-1].min() * 1.02
        rsi_higher_now = r.iloc[-1] > r.iloc[:-1].min() * 1.05
        return bool(price_low_now and rsi_higher_now)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MARKET INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────

def _safe_pct(symbol: str, period: str = "5d") -> float:
    for _ in range(3):
        try:
            df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
            if len(df) >= 2:
                return round((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100, 2)
        except Exception:
            time.sleep(0.5)
    return 0.0

def compute_fear_greed() -> dict:
    try:
        vix_df   = yf.Ticker("^INDIAVIX").history(period="5d",  interval="1d")
        nifty_df = yf.Ticker("^NSEI").history(period="30d", interval="1d")
        vix_now  = float(vix_df["Close"].iloc[-1]) if not vix_df.empty else 15
        nifty_mom = 0.0
        if len(nifty_df) >= 20:
            nifty_mom = (nifty_df["Close"].iloc[-1] / nifty_df["Close"].iloc[-20] - 1) * 100
        vix_score = max(0, min(100, 100 - (vix_now - 10) * 4))
        mom_score = max(0, min(100, 50 + nifty_mom * 3))
        score     = int(vix_score * 0.5 + mom_score * 0.5)
        if score >= 75:   label = "Extreme Greed"
        elif score >= 55: label = "Greed"
        elif score >= 45: label = "Neutral"
        elif score >= 25: label = "Fear"
        else:             label = "Extreme Fear"
        return {"score": score, "label": label, "vix": round(vix_now, 2)}
    except Exception:
        return {"score": 50, "label": "Neutral", "vix": 15.0}

def compute_sector_strength() -> list:
    sectors = [
        {"name": "IT",       "symbols": ["TCS.NS",        "INFY.NS",       "HCLTECH.NS"]},
        {"name": "Bank",     "symbols": ["HDFCBANK.NS",   "ICICIBANK.NS",  "SBIN.NS"]},
        {"name": "Auto",     "symbols": ["MARUTI.NS",     "TATAMOTORS.NS", "BAJAJ-AUTO.NS"]},
        {"name": "Pharma",   "symbols": ["SUNPHARMA.NS",  "DRREDDY.NS",    "CIPLA.NS"]},
        {"name": "FMCG",     "symbols": ["HINDUNILVR.NS", "ITC.NS",        "NESTLEIND.NS"]},
        {"name": "Metal",    "symbols": ["TATASTEEL.NS",  "HINDALCO.NS",   "JSWSTEEL.NS"]},
        {"name": "Energy",   "symbols": ["RELIANCE.NS",   "ONGC.NS",       "NTPC.NS"]},
        {"name": "Infra",    "symbols": ["LT.NS",         "ADANIPORTS.NS", "POWERGRID.NS"]},
    ]
    result = []
    for s in sectors:
        changes = [c for sym in s["symbols"] if (c := _safe_pct(sym)) != 0.0]
        avg_chg = round(sum(changes) / len(changes), 2) if changes else 0.0
        result.append({"name": s["name"], "change": avg_chg})
    return sorted(result, key=lambda x: x["change"], reverse=True)

def fetch_news() -> list:
    """Fetch real market news from Economic Times + Moneycontrol RSS (free, no API key)."""
    try:
        import feedparser
    except ImportError:
        return []

    FEEDS = [
        ("https://economictimes.indiatimes.com/markets/stocks/news/rssfeeds/2146842.cms", "Economic Times"),
        ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",           "ET Markets"),
        ("https://www.moneycontrol.com/rss/marketsnews.xml",                               "Moneycontrol"),
        ("https://www.moneycontrol.com/rss/latestnews.xml",                                "Moneycontrol"),
    ]
    KEYWORDS = [
        "stock", "market", "nifty", "sensex", "trade", "buy", "sell",
        "rally", "bull", "bear", "ipo", "result", "earning", "profit",
        "revenue", "rbi", "fed", "rate", "inflation", "rupee",
    ]
    seen, items = set(), []
    for url, source in FEEDS:
        try:
            import feedparser as fp
            feed = fp.parse(url)
            for e in feed.entries[:6]:
                title = e.get("title", "").strip()
                if not title or title in seen:
                    continue
                if not any(k in title.lower() for k in KEYWORDS):
                    continue
                seen.add(title)
                items.append({
                    "title":     title,
                    "publisher": source,
                    "link":      e.get("link", "#"),
                })
                if len(items) >= 8:
                    break
        except Exception:
            pass
        if len(items) >= 8:
            break
    return items

def market_overview() -> list:
    indices = [
        {"name": "NIFTY 50",   "symbol": "^NSEI"},
        {"name": "SENSEX",     "symbol": "^BSESN"},
        {"name": "NIFTY BANK", "symbol": "^NSEBANK"},
        {"name": "INDIA VIX",  "symbol": "^INDIAVIX"},
        {"name": "NIFTY IT",   "symbol": "^CNXIT"},
        {"name": "NIFTY MID",  "symbol": "^CNXMIDCAP"},
    ]
    result = []
    for idx in indices:
        for attempt in range(3):
            try:
                df = yf.Ticker(idx["symbol"]).history(period="5d", interval="1d", auto_adjust=True)
                if not df.empty and len(df) >= 2:
                    price = round(float(df["Close"].iloc[-1]), 2)
                    chg   = round((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100, 2)
                    result.append({"name": idx["name"], "price": price, "change": chg})
                    break
            except Exception:
                if attempt < 2:
                    time.sleep(1)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL ENGINE
# ─────────────────────────────────────────────────────────────────────────────

SIGNAL_THRESHOLD = 55
MIN_CANDLES      = 150
ATR_TARGET_MULT  = 2.5
ATR_SL_MULT      = 1.0
MAX_SIGNALS      = 5
MIN_AVG_VOLUME   = 50_000
MIN_PRICE        = 10.0

def _fetch_ohlcv(symbol: str) -> Optional[pd.DataFrame]:
    try:
        df = yf.Ticker(symbol).history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < MIN_CANDLES:
            return None
        df.dropna(inplace=True)
        if df["Volume"].tail(20).mean() < MIN_AVG_VOLUME:
            return None
        if float(df["Close"].iloc[-1]) < MIN_PRICE:
            return None
        return df
    except Exception:
        return None

def _days_to_earnings(symbol: str) -> Optional[int]:
    """Return calendar days until next earnings, or None if unknown/far away."""
    try:
        cal = yf.Ticker(symbol).calendar
        if cal is None or cal.empty:
            return None
        best = None
        for col in cal.columns:
            if 'earnings' in col.lower():
                dates = cal[col].dropna()
                for d in dates:
                    if hasattr(d, 'date'):
                        d = d.date()
                    delta = (d - datetime.now().date()).days
                    if delta >= -1 and (best is None or delta < best):
                        best = delta
        return best
    except Exception:
        return None


def _nifty_context():
    """Fetch Nifty 50 close series + trend status once per scan (Kill 5, Booster 2)."""
    try:
        df = yf.Ticker("^NSEI").history(period="1y", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 60:
            return None, True
        close = df["Close"].dropna()
        ema50 = close.ewm(span=50, adjust=False).mean()
        positive = bool(close.iloc[-1] > ema50.iloc[-1])
        return close, positive
    except Exception:
        return None, True


def _score_stock(df: pd.DataFrame, symbol: str, name: str, sector: str,
                  nifty_close=None, nifty_positive: bool = True) -> Optional[dict]:
    if len(df) < 210:
        return None

    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    openp  = df["Open"]
    volume = df["Volume"]

    ema9   = close.ewm(span=9,   adjust=False).mean()
    ema21  = close.ewm(span=21,  adjust=False).mean()
    ema50  = close.ewm(span=50,  adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    rsi_s             = rsi(close, 14)
    macd_line, sig, _ = macd(close)
    atr_s             = atr(df, 14)
    vol_r             = volume_ratio(volume, 20)

    price_now  = float(close.iloc[-1])
    rsi_now    = float(rsi_s.iloc[-1])
    ema9_now   = float(ema9.iloc[-1])
    ema21_now  = float(ema21.iloc[-1])
    ema50_now  = float(ema50.iloc[-1])
    ema200_now = float(ema200.iloc[-1])
    atr_now    = float(atr_s.iloc[-1]) if not np.isnan(atr_s.iloc[-1]) else 0.0
    vol_now    = float(vol_r.iloc[-1]) if not np.isnan(vol_r.iloc[-1]) else 0.0
    avg_vol20  = float(volume.tail(20).mean())
    high_52w   = float(high.tail(252).max())

    # ═══════════════════════ STAGE 1 — HARD KILL SWITCHES ═══════════════════════
    if vol_now < 1.5:
        return None
    if high_52w > 0 and price_now >= high_52w * 0.92:
        return None
    days_to_earn = _days_to_earnings(symbol)
    if days_to_earn is not None and days_to_earn <= 15:
        return None
    if avg_vol20 < 800_000:
        return None
    if not nifty_positive:
        return None
    if price_now < 80:
        return None
    if len(close) >= 4:
        drop_3d = (price_now / float(close.iloc[-4]) - 1) * 100
        if drop_3d <= -5:
            return None
    if atr_now < 5:
        return None

    # ═══════════════════════ STAGE 2 — CORE SCORING (max 60) ═══════════════════
    score = 0

    pct_above_200 = (price_now / ema200_now - 1) * 100 if ema200_now else 0
    c_ema200 = pct_above_200 >= 5
    if c_ema200: score += 10

    c_stack = ema9_now > ema21_now > ema50_now
    if c_stack: score += 10

    macd_cross_day = None
    for k in range(1, 4):
        if len(macd_line) <= k:
            break
        m_now, s_now   = float(macd_line.iloc[-k]),   float(sig.iloc[-k])
        m_prev, s_prev = float(macd_line.iloc[-k-1]), float(sig.iloc[-k-1])
        if m_prev <= s_prev and m_now > s_now:
            macd_cross_day = k
            break
    c_macd = macd_cross_day is not None
    if c_macd: score += 10

    c_rsi = 45 <= rsi_now <= 63
    if c_rsi: score += 10

    c_vol = vol_now >= 1.5
    if c_vol: score += 10

    c_ema21 = price_now > ema21_now
    if c_ema21: score += 10

    if score < 50:
        return None

    # ═══════════════════════ STAGE 3 — QUALITY BOOSTERS (max 40) ═══════════════
    boost = 0

    o_now, c_now, h_now, l_now = float(openp.iloc[-1]), price_now, float(high.iloc[-1]), float(low.iloc[-1])
    rng  = h_now - l_now
    body = c_now - o_now
    c_candle = c_now > o_now and rng > 0 and (body / rng) >= 0.6
    if c_candle: boost += 10

    c_relstrength = False
    if nifty_close is not None and len(nifty_close) >= 11 and len(close) >= 11:
        stock_chg = (close.iloc[-1] / close.iloc[-11] - 1) * 100
        nifty_chg = (nifty_close.iloc[-1] / nifty_close.iloc[-11] - 1) * 100
        c_relstrength = bool(stock_chg > nifty_chg)
    if c_relstrength: boost += 10

    pct_below_high = (1 - price_now / high_52w) * 100 if high_52w else 0
    c_farfromhigh = pct_below_high > 15
    if c_farfromhigh: boost += 10

    vol_prev = float(vol_r.iloc[-2]) if len(vol_r) >= 2 and not np.isnan(vol_r.iloc[-2]) else 0.0
    c_2dayvol = vol_now >= 1.5 and vol_prev >= 1.2
    if c_2dayvol: boost += 10

    final_score = score + boost
    if final_score < 70:
        return None

    # ═══════════════════════ STAGE 4 — TARGET & R:R ═════════════════════════════
    entry_low  = round(price_now * 0.995, 2)
    entry_high = round(price_now * 1.005, 2)

    raw_target = price_now + 2.0 * atr_now
    r50  = (int(price_now // 50) + 1) * 50
    r100 = (int(price_now // 100) + 1) * 100
    round_ceiling = min(r50, r100)
    swing_high    = float(high.tail(20).max())
    ceiling_candidates = [c for c in [high_52w, round_ceiling, swing_high] if c > price_now]
    ceiling = min(ceiling_candidates) if ceiling_candidates else raw_target

    target = raw_target
    if ceiling <= raw_target * 1.03:
        target = ceiling * 0.98
    target = round(target, 2)

    sl_atr   = price_now - 1.0 * atr_now
    sl_min4  = price_now * 0.96
    stop_loss = round(min(sl_atr, sl_min4), 2)

    risk   = price_now - stop_loss
    reward = target - price_now
    rr     = round(reward / risk, 2) if risk > 0 else 0
    if rr < 1.8:
        return None

    pct_to_target = round((target - price_now) / price_now * 100, 2)
    pct_to_sl     = round((price_now - stop_loss) / price_now * 100, 2)
    clean  = symbol.replace(".NS", "").replace(".BO", "")
    prefix = "BSE:" if symbol.endswith(".BO") else "NSE:"

    conditions = [
        f"{'✓' if c_ema200 else '✗'} 200 EMA ({pct_above_200:.1f}% above)",
        f"{'✓' if c_macd else '✗'} Fresh MACD cross (within 3 days)",
        f"{'✓' if c_rsi else '✗'} RSI {rsi_now:.1f} in 45–63 zone",
        f"{'✓' if c_vol else '✗'} Volume {vol_now:.1f}x average",
        f"{'✓' if c_stack else '✗'} EMA stack 9>21>50",
        f"{'✓' if c_ema21 else '✗'} 21 EMA closed above",
        f"✓ Nifty 50 trend: POSITIVE",
        f"✓ Days to earnings: {days_to_earn if days_to_earn is not None else '60+'} days",
    ]

    return {
        "id":            abs(hash(symbol + datetime.now().strftime("%Y-%m-%d"))) % 100_000,
        "symbol":        f"{prefix}{clean}",
        "ticker":        symbol,
        "name":          name,
        "sector":        sector,
        "type":          "BULLISH",
        "confidence":    min(final_score, 100),
        "score":         final_score,
        "entry":         f"₹{entry_low:.0f} – ₹{entry_high:.0f}",
        "entryLow":      entry_low,
        "entryHigh":     entry_high,
        "target":        f"₹{target:.0f}",
        "targetFloat":   target,
        "stoploss":      f"₹{stop_loss:.0f}",
        "stopFloat":     stop_loss,
        "rrRatio":       rr,
        "pctToTarget":   pct_to_target,
        "pctToSL":       pct_to_sl,
        "currentPrice":  round(price_now, 2),
        "atr":           round(atr_now, 2),
        "rsi":           round(rsi_now, 2),
        "volumeRatio":   round(vol_now, 2),
        "days":          "5–8",
        "high52w":       round(high_52w, 2),
        "resistance":    round(ceiling, 2),
        "reason":        conditions[0] if conditions else "Multi-indicator confluence",
        "conditions":    conditions,
        "generatedAt":   datetime.now().isoformat(),
    }

def scan_for_signals(stocks: list) -> dict:
    # Step 0 — Nifty 50 trend context, fetched once (Kill 5 + Booster 2)
    nifty_close, nifty_positive = _nifty_context()
    if not nifty_positive:
        logger.info("⏸ Nifty 50 below 50 EMA — market regime unfavorable, no signals will fire")

    # Step 1 — pre-filter: keep only liquid, priced stocks (price>20, avgvol>200k)
    filtered = pre_filter(stocks)
    if not filtered:
        logger.warning("Pre-filter returned 0 stocks — falling back to full list")
        filtered = stocks

    # Build symbol → metadata lookup for use after batch download
    meta = {s["symbol"]: s for s in filtered}
    symbols = list(meta.keys())

    # Step 2 — batch-download full OHLCV in groups of 50
    # Smaller batches + 0.5s pause between them keep uvicorn responsive
    # during the scan so the preview proxy never loses the connection.
    raw_signals = []
    if nifty_positive:
        for i in range(0, len(symbols), 50):
            chunk = symbols[i:i + 50]
            data = batch_download(chunk, period="1y")
            batch_scored = 0
            for sym, df in data.items():
                stock = meta.get(sym, {})
                try:
                    res = _score_stock(df, sym, stock.get("name", sym), stock.get("sector", "NSE Equity"),
                                        nifty_close, nifty_positive)
                except Exception as e:
                    logger.warning("Skipping %s — scoring error: %s", sym, e)
                    continue
                if res:
                    raw_signals.append(res)
                    batch_scored += 1
                    logger.info("✓ SIGNAL %s  score=%d  conf=%d%%",
                                res["symbol"], res["score"], res["confidence"])
            logger.info("Batch %d/%d — downloaded %d, scored %d signal(s) so far: %d",
                        i // 50 + 1, -(-len(symbols) // 50), len(data), batch_scored, len(raw_signals))
            time.sleep(0.5)  # yield to uvicorn event loop between batches

    # Step 3 — Stage 6: sort by final score, top MAX_SIGNALS only
    raw_signals.sort(key=lambda x: x["score"], reverse=True)
    final = raw_signals[:MAX_SIGNALS]
    extra = max(0, len(raw_signals) - len(final))
    note = None
    if extra > 0:
        note = f"{extra} more stock{'s' if extra != 1 else ''} passed but ranked below"
    elif not final:
        note = "No quality setups today. Market not giving clean entries."
    return {"signals": final, "note": note, "niftyPositive": nifty_positive}


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="AI Khan Backend", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

_cache: dict     = {}
_scan_lock       = threading.Lock()

def _cached(key: str, ttl: int, fn, *args):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    data = fn(*args)
    _cache[key] = {"data": data, "ts": time.time()}
    return data

def _background_scan(send_alert_on_signals: bool = False):
    with _scan_lock:
        universe = fetch_all_nse_stocks()
        logger.info("▶ Starting full scan (%d stocks)…", len(universe))
        t0      = time.time()
        result  = scan_for_signals(universe)
        signals = result["signals"]
        elapsed = round(time.time() - t0, 1)
        _cache["signals"] = {
            "data": {
                "signals":       signals,
                "count":         len(signals),
                "note":          result.get("note"),
                "niftyPositive": result.get("niftyPositive", True),
                "scannedAt":     datetime.now().isoformat(),
                "scanTimeS":     elapsed,
                "universe":      len(universe),
            },
            "ts": time.time(),
        }
        logger.info("✅ Scan done in %.1fs — %d signals found", elapsed, len(signals))
        if send_alert_on_signals and signals:
            alert_status = send_alerts(signals)
            _scheduler_state["lastAlertStatus"] = alert_status
            _scheduler_state["lastAlertAt"] = datetime.now().isoformat()
            logger.info("📣 Alerts sent — Telegram:%s  Email:%s",
                        alert_status["telegram"], alert_status["email"])


# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULER — auto-scan every 30 min during market hours, 2h overnight
# ─────────────────────────────────────────────────────────────────────────────

_scheduler_state = {
    "running":        False,
    "lastScanAt":     None,
    "nextScanAt":     None,
    "scanCount":      0,
    "lastAlertAt":    None,
    "lastAlertStatus": None,
}

def _scheduler_loop():
    """Runs forever in a background thread. Triggers scans on schedule."""
    import pytz
    IST = pytz.timezone("Asia/Kolkata")

    _scheduler_state["running"] = True
    logger.info("🕐 Scheduler started")

    while True:
        now_ist = datetime.now(IST)
        hour    = now_ist.hour

        # Market hours: 9:00–15:30 IST → scan every 30 min
        # Pre/post market: 8:00–9:00 and 15:30–17:00 → scan every 60 min
        # Overnight: 17:00–8:00 → scan every 2 hours (catch any after-hours setups)
        if 9 <= hour < 16:
            interval_min = 30
        elif (hour == 8) or (16 <= hour < 17):
            interval_min = 60
        else:
            interval_min = 120

        next_scan = datetime.now(IST).replace(second=0, microsecond=0)
        # Round up to next interval boundary
        mins = next_scan.minute
        wait_mins = interval_min - (mins % interval_min) if (mins % interval_min) != 0 else interval_min
        import datetime as dt_mod
        next_scan = next_scan + dt_mod.timedelta(minutes=wait_mins)
        _scheduler_state["nextScanAt"] = next_scan.isoformat()

        sleep_secs = max(60, wait_mins * 60)
        logger.info("⏱ Next auto-scan in %d min at %s IST", wait_mins,
                    next_scan.strftime("%H:%M"))
        time.sleep(sleep_secs)

        # Run scan and send alerts if signals found
        _scheduler_state["lastScanAt"] = datetime.now().isoformat()
        _scheduler_state["scanCount"] += 1
        logger.info("🔄 Scheduler triggering scan #%d", _scheduler_state["scanCount"])
        if not _scan_lock.locked():
            _background_scan(send_alert_on_signals=True)
        else:
            logger.info("⏸ Scan already running — skipping scheduled scan")


@app.on_event("startup")
def startup():
    # Initial scan on boot (no alert — first run)
    threading.Thread(target=_background_scan, daemon=True).start()
    # Start the recurring scheduler
    threading.Thread(target=_scheduler_loop, daemon=True).start()

@app.get("/")
def root():
    return FileResponse(
        "static/index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

@app.get("/ping")
def ping():
    return {"status": "alive"}

@app.get("/api/health")
def health():
    return {"status": "online", "version": "3.0.0", "universe": len(ALL_STOCKS)}

@app.get("/api/signals")
def get_signals():
    entry = _cache.get("signals")
    if not entry:
        return {"status": "scanning", "signals": [], "count": 0}
    return {"status": "ok", **entry["data"]}

@app.get("/api/signals/refresh")
def refresh(background_tasks: BackgroundTasks):
    if _scan_lock.locked():
        return {"status": "already_scanning"}
    _cache.pop("signals", None)
    background_tasks.add_task(_background_scan)
    return {"status": "queued"}

@app.get("/api/market-intel")
def get_intel():
    return {
        "status":    "ok",
        "fearGreed": _cached("fear_greed", 900, compute_fear_greed),
        "sectors":   _cached("sectors",    900, compute_sector_strength),
    }

@app.get("/api/news")
def get_news():
    return {"status": "ok", "news": _cached("news", 600, fetch_news)}

@app.get("/api/overview")
def get_overview():
    return {"status": "ok", "indices": _cached("overview", 300, market_overview)}

@app.get("/api/scheduler/status")
def scheduler_status():
    import os
    return {
        "status": "ok",
        **_scheduler_state,
        "telegramConfigured": bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
        "emailConfigured":    bool(os.environ.get("EMAIL_SENDER") and os.environ.get("EMAIL_PASSWORD") and os.environ.get("EMAIL_RECIPIENT")),
        "emailRecipient":     os.environ.get("EMAIL_RECIPIENT", ""),
        "telegramChatId":     os.environ.get("TELEGRAM_CHAT_ID", ""),
    }

@app.post("/api/alerts/test/telegram")
def test_telegram():
    result = send_telegram_test()
    return {"status": "ok" if result["ok"] else "error", **result}

@app.post("/api/alerts/test/email")
def test_email():
    result = send_email_test()
    return {"status": "ok" if result["ok"] else "error", **result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
