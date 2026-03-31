import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime

# ── Sectores S&P 500 y sus principales componentes ───────────────
SECTORS = {
    "XLI":  {
        "name": "Industrials",
        "components": ["GE","RTX","HON","UNP","CAT","DE","LMT","ETN","EMR","WM","ITW","PH","GD","TDG","CTAS"],
    },
    "XLV":  {
        "name": "Health Care",
        "components": ["UNH","JNJ","LLY","ABBV","MRK","TMO","ABT","DHR","PFE","BMY","AMGN","ISRG","MDT","CVS","ELV"],
    },
    "XLK":  {
        "name": "Technology",
        "components": ["AAPL","NVDA","MSFT","AVGO","ORCL","AMD","ADBE","CSCO","ACN","QCOM","TXN","AMAT","NOW","INTU"],
    },
    "XLC":  {
        "name": "Communication Services",
        "components": ["META","GOOGL","NFLX","T","VZ","TMUS","DIS","EA","TTWO","OMC","CHTR","WBD"],
    },
    "XLY":  {
        "name": "Consumer Discretionary",
        "components": ["AMZN","TSLA","HD","MCD","NKE","LOW","BKNG","TJX","SBUX","CMG","ROST","DHI"],
    },
    "XLP":  {
        "name": "Consumer Staples",
        "components": ["PG","COST","WMT","KO","PEP","PM","MO","MDLZ","CL","STZ","KMB","EL"],
    },
    "XLE":  {
        "name": "Energy",
        "components": ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","KMI","WMB","DVN"],
    },
    "XLB":  {
        "name": "Materials",
        "components": ["LIN","APD","FCX","NEM","NUE","VMC","MLM","PPG","ECL","IFF","ALB","CF"],
    },
    "XLF":  {
        "name": "Financials",
        "components": ["BRK-B","JPM","BAC","WFC","GS","MS","BLK","SCHW","AXP","SPGI","CB","MMC"],
    },
    "XLU":  {
        "name": "Utilities",
        "components": ["NEE","SO","DUK","AEP","SRE","D","EXC","XEL","AWK","ES","WEC","ETR"],
    },
    "XLRE": {
        "name": "Real Estate",
        "components": ["PLD","AMT","EQIX","CCI","PSA","WELL","DLR","O","AVB","EQR","SPG","VICI"],
    },
}

# ── Nombres de tickers ────────────────────────────────────────────
NAMES = {
    # Sector ETFs
    "XLI":"SPDR Industrials","XLV":"SPDR Health Care","XLK":"SPDR Technology",
    "XLC":"SPDR Comm. Services","XLY":"SPDR Cons. Discret.","XLP":"SPDR Cons. Staples",
    "XLE":"SPDR Energy","XLB":"SPDR Materials","XLF":"SPDR Financials",
    "XLU":"SPDR Utilities","XLRE":"SPDR Real Estate",
    # Industrials
    "GE":"GE Aerospace","RTX":"RTX Corp","HON":"Honeywell","UNP":"Union Pacific",
    "CAT":"Caterpillar","DE":"Deere & Co","LMT":"Lockheed Martin","ETN":"Eaton Corp",
    "EMR":"Emerson Electric","WM":"Waste Management","ITW":"Illinois Tool Works",
    "PH":"Parker-Hannifin","GD":"General Dynamics","TDG":"TransDigm","CTAS":"Cintas",
    # Health Care
    "UNH":"UnitedHealth","JNJ":"Johnson & Johnson","LLY":"Eli Lilly","ABBV":"AbbVie",
    "MRK":"Merck","TMO":"Thermo Fisher","ABT":"Abbott Labs","DHR":"Danaher",
    "PFE":"Pfizer","BMY":"Bristol-Myers","AMGN":"Amgen","ISRG":"Intuitive Surgical",
    "MDT":"Medtronic","CVS":"CVS Health","ELV":"Elevance Health",
    # Technology
    "AAPL":"Apple","NVDA":"NVIDIA","MSFT":"Microsoft","AVGO":"Broadcom",
    "ORCL":"Oracle","AMD":"AMD","ADBE":"Adobe","CSCO":"Cisco",
    "ACN":"Accenture","QCOM":"Qualcomm","TXN":"Texas Instruments",
    "AMAT":"Applied Materials","NOW":"ServiceNow","INTU":"Intuit",
    # Communication
    "META":"Meta Platforms","GOOGL":"Alphabet","NFLX":"Netflix","T":"AT&T",
    "VZ":"Verizon","TMUS":"T-Mobile","DIS":"Walt Disney","EA":"Electronic Arts",
    "TTWO":"Take-Two","OMC":"Omnicom","CHTR":"Charter Comm.","WBD":"Warner Bros",
    # Consumer Discretionary
    "AMZN":"Amazon","TSLA":"Tesla","HD":"Home Depot","MCD":"McDonald's",
    "NKE":"Nike","LOW":"Lowe's","BKNG":"Booking Holdings","TJX":"TJX Companies",
    "SBUX":"Starbucks","CMG":"Chipotle","ROST":"Ross Stores","DHI":"D.R. Horton",
    # Consumer Staples
    "PG":"Procter & Gamble","COST":"Costco","WMT":"Walmart","KO":"Coca-Cola",
    "PEP":"PepsiCo","PM":"Philip Morris","MO":"Altria","MDLZ":"Mondelez",
    "CL":"Colgate-Palmolive","STZ":"Constellation Brands","KMB":"Kimberly-Clark","EL":"Estee Lauder",
    # Energy
    "XOM":"ExxonMobil","CVX":"Chevron","COP":"ConocoPhillips","EOG":"EOG Resources",
    "SLB":"SLB","MPC":"Marathon Petroleum","PSX":"Phillips 66","VLO":"Valero Energy",
    "OXY":"Occidental","KMI":"Kinder Morgan","WMB":"Williams Cos","DVN":"Devon Energy",
    # Materials
    "LIN":"Linde","APD":"Air Products","FCX":"Freeport-McMoRan","NEM":"Newmont",
    "NUE":"Nucor","VMC":"Vulcan Materials","MLM":"Martin Marietta","PPG":"PPG Industries",
    "ECL":"Ecolab","IFF":"Intl Flavors","ALB":"Albemarle","CF":"CF Industries",
    # Financials
    "BRK-B":"Berkshire Hathaway","JPM":"JPMorgan Chase","BAC":"Bank of America",
    "WFC":"Wells Fargo","GS":"Goldman Sachs","MS":"Morgan Stanley","BLK":"BlackRock",
    "SCHW":"Charles Schwab","AXP":"American Express","SPGI":"S&P Global",
    "CB":"Chubb","MMC":"Marsh & McLennan",
    # Utilities
    "NEE":"NextEra Energy","SO":"Southern Co","DUK":"Duke Energy","AEP":"Am. Electric Power",
    "SRE":"Sempra","D":"Dominion Energy","EXC":"Exelon","XEL":"Xcel Energy",
    "AWK":"American Water","ES":"Eversource","WEC":"WEC Energy","ETR":"Entergy",
    # Real Estate
    "PLD":"Prologis","AMT":"American Tower","EQIX":"Equinix","CCI":"Crown Castle",
    "PSA":"Public Storage","WELL":"Welltower","DLR":"Digital Realty","O":"Realty Income",
    "AVB":"AvalonBay","EQR":"Equity Residential","SPG":"Simon Property","VICI":"VICI Properties",
}

# ── Caché simple para evitar rate limiting ────────────────────────
_cache      = {}
_cache_time = {}
CACHE_TTL   = 300   # 5 minutos


def _pct(series, periods):
    """Retorno porcentual entre posición -1 y -periods."""
    try:
        if len(series) <= periods:
            return None
        val = round((float(series.iloc[-1]) / float(series.iloc[-periods]) - 1) * 100, 2)
        return val
    except Exception:
        return None


def _pct_ytd(series):
    """Retorno YTD desde el primer día del año en curso."""
    try:
        year_start = datetime(datetime.today().year, 1, 1)
        ytd_series = series[series.index >= pd.Timestamp(year_start, tz=series.index.tz)]
        if len(ytd_series) < 2:
            return None
        return round((float(ytd_series.iloc[-1]) / float(ytd_series.iloc[0]) - 1) * 100, 2)
    except Exception:
        return None


def _rs(ticker_1y, spx_1y):
    """RS simplificado: rendimiento relativo al SPX, escala 1-99."""
    try:
        if spx_1y is None or spx_1y == 0 or ticker_1y is None:
            return None
        raw = (1 + ticker_1y / 100) / (1 + spx_1y / 100) * 50
        return round(min(99, max(1, raw)), 1)
    except Exception:
        return None


def get_sector_data(sector_key):
    """Descarga y calcula métricas para un sector y sus componentes."""
    now = time.time()
    if sector_key in _cache and now - _cache_time.get(sector_key, 0) < CACHE_TTL:
        return _cache[sector_key]

    sector   = SECTORS[sector_key]
    tickers  = [sector_key] + sector["components"] + ["^GSPC"]

    try:
        raw      = yf.download(tickers, period="1y", progress=False, auto_adjust=True)
        close    = raw["Close"]

        spx_1y   = _pct(close["^GSPC"].dropna(), 252)
        rows     = []

        display_tickers = [sector_key] + sector["components"]

        for ticker in display_tickers:
            try:
                s    = close[ticker].dropna()
                if s.empty:
                    continue
                price = round(float(s.iloc[-1]), 2)
                d1    = _pct(s, 1)
                w1    = _pct(s, 5)
                m1    = _pct(s, 21)
                ytd   = _pct_ytd(s)
                y1    = _pct(s, 252)
                rs    = _rs(y1, spx_1y)

                rows.append({
                    "ticker":  ticker,
                    "name":    NAMES.get(ticker, ticker),
                    "price":   price,
                    "rs":      rs,
                    "d1":      d1,
                    "w1":      w1,
                    "m1":      m1,
                    "ytd":     ytd,
                    "y1":      y1,
                })
            except Exception:
                continue

        _cache[sector_key]      = rows
        _cache_time[sector_key] = now
        return rows

    except Exception:
        return []
