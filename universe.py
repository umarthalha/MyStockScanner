import requests
import pandas as pd
from io import StringIO

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
    {"symbol": "ANGELONE.NS",   "name": "Angel One",                   "sector": "Finance"},
    {"symbol": "ASTRAL.NS",     "name": "Astral Ltd",                  "sector": "Plastics"},
    {"symbol": "BLUESTARCO.NS", "name": "Blue Star",                   "sector": "Consumer Electric"},
    {"symbol": "CANFINHOME.NS", "name": "Can Fin Homes",               "sector": "Housing Finance"},
    {"symbol": "CROMPTON.NS",   "name": "Crompton Greaves",            "sector": "Consumer Electric"},
    {"symbol": "DELHIVERY.NS",  "name": "Delhivery",                   "sector": "Logistics"},
    {"symbol": "EMAMILTD.NS",   "name": "Emami Ltd",                   "sector": "FMCG"},
    {"symbol": "GLAND.NS",      "name": "Gland Pharma",                "sector": "Pharma"},
    {"symbol": "HAPPSTMNDS.NS", "name": "Happiest Minds",              "sector": "IT"},
    {"symbol": "INDHOTEL.NS",   "name": "Indian Hotels (Taj)",         "sector": "Hospitality"},
    {"symbol": "KAYNES.NS",     "name": "Kaynes Technology",           "sector": "Electronics"},
    {"symbol": "KFINTECH.NS",   "name": "KFin Technologies",           "sector": "Finance"},
    {"symbol": "LAURUSLABS.NS", "name": "Laurus Labs",                 "sector": "Pharma"},
    {"symbol": "MASTEK.NS",     "name": "Mastek",                      "sector": "IT"},
    {"symbol": "MAXHEALTH.NS",  "name": "Max Healthcare",              "sector": "Healthcare"},
    {"symbol": "METROPOLIS.NS", "name": "Metropolis Healthcare",       "sector": "Healthcare"},
    {"symbol": "NAVINFLUOR.NS", "name": "Navin Fluorine",              "sector": "Chemicals"},
    {"symbol": "RITES.NS",      "name": "RITES Ltd",                   "sector": "Infrastructure"},
    {"symbol": "SOLARINDS.NS",  "name": "Solar Industries",            "sector": "Defence"},
    {"symbol": "SONACOMS.NS",   "name": "Sona BLW Precision",          "sector": "Auto Ancillary"},
    {"symbol": "STAR.NS",       "name": "Star Health Insurance",       "sector": "Insurance"},
    {"symbol": "TATACHEM.NS",   "name": "Tata Chemicals",              "sector": "Chemicals"},
    {"symbol": "TATACOMM.NS",   "name": "Tata Communications",         "sector": "Telecom"},
    {"symbol": "TATAELXSI.NS",  "name": "Tata Elxsi",                  "sector": "IT"},
    {"symbol": "TRIDENT.NS",    "name": "Trident Ltd",                 "sector": "Textiles"},
    {"symbol": "VGUARD.NS",     "name": "V-Guard Industries",          "sector": "Consumer Electric"},
    {"symbol": "WELCORP.NS",    "name": "Welspun Corp",                "sector": "Metal"},
    {"symbol": "ZENTEC.NS",     "name": "Zen Technologies",            "sector": "Defence"},
    {"symbol": "BIKAJI.NS",     "name": "Bikaji Foods",                "sector": "FMCG"},
    {"symbol": "CLEAN.NS",      "name": "Clean Science Tech",          "sector": "Chemicals"},
    {"symbol": "CONCORDBIO.NS", "name": "Concord Biotech",             "sector": "Pharma"},
    {"symbol": "JKTYRE.NS",     "name": "JK Tyre",                     "sector": "Auto Ancillary"},
    {"symbol": "KANSAINER.NS",  "name": "Kansai Nerolac",              "sector": "Paints"},
    {"symbol": "ROUTE.NS",      "name": "Route Mobile",                "sector": "IT"},
    {"symbol": "SWSOLAR.NS",    "name": "Sterling Wilson Solar",       "sector": "Renewable Energy"},
    {"symbol": "TIMKEN.NS",     "name": "Timken India",                "sector": "Industrial"},
    {"symbol": "NETWORK18.NS",  "name": "Network18",                   "sector": "Media"},
    {"symbol": "CRISIL.NS",     "name": "CRISIL",                      "sector": "Finance"},
    {"symbol": "ELECON.NS",     "name": "Elecon Engineering",          "sector": "Capital Goods"},
    {"symbol": "ADANIPOWER.BO", "name": "Adani Power",                 "sector": "Power"},
    {"symbol": "CESC.BO",       "name": "CESC Limited",                "sector": "Power"},
    {"symbol": "CONCOR.BO",     "name": "Container Corp",              "sector": "Logistics"},
    {"symbol": "DLF.BO",        "name": "DLF Limited",                 "sector": "Real Estate"},
    {"symbol": "GODREJPROP.BO", "name": "Godrej Properties",           "sector": "Real Estate"},
    {"symbol": "HDFCAMC.BO",    "name": "HDFC AMC",                    "sector": "Finance"},
    {"symbol": "IOC.BO",        "name": "Indian Oil Corp",             "sector": "Oil & Gas"},
    {"symbol": "JSWENERGY.BO",  "name": "JSW Energy",                  "sector": "Power"},
    {"symbol": "KALYANKJIL.BO", "name": "Kalyan Jewellers",            "sector": "Retail"},
    {"symbol": "LALPATHLAB.BO", "name": "Dr Lal PathLabs",             "sector": "Healthcare"},
    {"symbol": "MAZDOCK.BO",    "name": "Mazagon Dock",                "sector": "Defence"},
    {"symbol": "MRF.BO",        "name": "MRF",                         "sector": "Auto Ancillary"},
    {"symbol": "NAUKRI.BO",     "name": "Info Edge (Naukri)",          "sector": "Internet"},
    {"symbol": "OBEROIRLTY.BO", "name": "Oberoi Realty",               "sector": "Real Estate"},
    {"symbol": "PAGEIND.BO",    "name": "Page Industries",             "sector": "Apparel"},
    {"symbol": "SBICARD.BO",    "name": "SBI Cards",                   "sector": "Finance"},
    {"symbol": "SJVN.BO",       "name": "SJVN Limited",                "sector": "Power"},
    {"symbol": "SUZLON.BO",     "name": "Suzlon Energy",               "sector": "Renewable Energy"},
    {"symbol": "TORNTPOWER.BO", "name": "Torrent Power",               "sector": "Power"},
    {"symbol": "UNIONBANK.BO",  "name": "Union Bank",                  "sector": "Banking"},
    {"symbol": "VARUNBEV.BO",   "name": "Varun Beverages",             "sector": "Beverages"},
    {"symbol": "ZEEL.BO",       "name": "Zee Entertainment",           "sector": "Media"},
    {"symbol": "SUPREMEIND.BO", "name": "Supreme Industries",          "sector": "Plastics"},
    {"symbol": "IREDA.BO",      "name": "IREDA",                       "sector": "Finance"},
    {"symbol": "INOXWIND.BO",   "name": "Inox Wind",                   "sector": "Renewable Energy"},
    {"symbol": "INDIANB.BO",    "name": "Indian Bank",                 "sector": "Banking"},
]


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.5",
}

# NSE index constituent CSVs — each has Symbol + Industry columns
_INDEX_URLS = [
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
    "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "https://archives.nseindia.com/content/indices/ind_niftylargemidcap250list.csv",
]


def fetch_sector_map() -> dict:
    """
    Returns {SYMBOL: industry_string} by downloading NSE index
    constituent CSVs that include an 'Industry' column.
    """
    sector_map: dict = {}
    for url in _INDEX_URLS:
        try:
            r = requests.get(url, headers=_HEADERS, timeout=20)
            if r.status_code != 200:
                continue
            df = pd.read_csv(StringIO(r.text))
            df.columns = df.columns.str.strip()
            if "Symbol" not in df.columns or "Industry" not in df.columns:
                continue
            for _, row in df.iterrows():
                sym = str(row["Symbol"]).strip()
                ind = str(row["Industry"]).strip()
                if sym and ind and ind.lower() not in ("nan", ""):
                    sector_map.setdefault(sym, ind)
        except Exception as e:
            print(f"Sector map fetch failed ({url}): {e}")
    return sector_map


def fetch_all_nse_stocks() -> list:
    """
    Fetches all NSE EQ-series stocks and enriches each with a real
    industry/sector from NSE index constituent files.
    Falls back to NIFTY200_STOCKS if the primary fetch fails.
    """
    sector_map = fetch_sector_map()

    try:
        r = requests.get(
            "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
            headers=_HEADERS,
            timeout=30,
        )
        if r.status_code == 200:
            df = pd.read_csv(StringIO(r.text))
            df.columns = df.columns.str.strip()
            df = df[df["SERIES"].str.strip() == "EQ"]
            stocks = []
            for _, row in df.iterrows():
                sym  = str(row["SYMBOL"]).strip()
                name = str(row["NAME OF COMPANY"]).strip()
                sector = sector_map.get(sym, "NSE Equity")
                stocks.append({
                    "symbol": f"{sym}.NS",
                    "name":   name,
                    "sector": sector,
                })
            if len(stocks) > 100:
                print(f"Universe: {len(stocks)} stocks fetched, "
                      f"{sum(1 for s in stocks if s['sector'] != 'NSE Equity')} with sector data")
                return stocks
    except Exception as e:
        print(f"NSE fetch failed: {e}")

    return NIFTY200_STOCKS
