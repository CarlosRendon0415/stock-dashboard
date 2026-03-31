import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime

# ── ETFs por sector (sub-sector ETFs, no acciones individuales) ──
SECTORS = {
    "XLK": {
        "name": "Technology",
        "components": ["SOXX", "IGV", "SKYY", "HACK", "PNQI", "AIQ", "ROBO", "WCLD"],
    },
    "XLV": {
        "name": "Health Care",
        "components": ["XBI", "IBB", "IHI", "XPH", "ARKG", "IHF", "IDNA"],
    },
    "XLF": {
        "name": "Financials",
        "components": ["KRE", "KBE", "IAK", "IAI", "KBWB", "KBWR", "IPAY"],
    },
    "XLE": {
        "name": "Energy",
        "components": ["XOP", "OIH", "TAN", "ICLN", "AMLP", "FCG"],
    },
    "XLI": {
        "name": "Industrials",
        "components": ["ITA", "XTN", "JETS", "ROAD", "SAIA"],
    },
    "XLY": {
        "name": "Consumer Discretionary",
        "components": ["XRT", "ONLN", "BETZ", "GENZ", "CARZ"],
    },
    "XLP": {
        "name": "Consumer Staples",
        "components": ["PBJ", "FTXG", "VDC"],
    },
    "XLB": {
        "name": "Materials",
        "components": ["GDX", "SLX", "LIT", "COPX", "PAVE", "REMX"],
    },
    "XLC": {
        "name": "Comm. Services",
        "components": ["FIVG", "SOCL", "NERD", "ESPO"],
    },
    "XLU": {
        "name": "Utilities",
        "components": ["FUTY", "UTES", "FAN", "YLCO"],
    },
    "XLRE": {
        "name": "Real Estate",
        "components": ["VNQ", "REZ", "SRVR", "INDS", "REM"],
    },
}

# ── Nombres descriptivos ─────────────────────────────────────────
NAMES = {
    # Sector ETFs
    "XLK":  "SPDR Technology",
    "XLV":  "SPDR Health Care",
    "XLF":  "SPDR Financials",
    "XLE":  "SPDR Energy",
    "XLI":  "SPDR Industrials",
    "XLY":  "SPDR Cons. Discretionary",
    "XLP":  "SPDR Cons. Staples",
    "XLB":  "SPDR Materials",
    "XLC":  "SPDR Comm. Services",
    "XLU":  "SPDR Utilities",
    "XLRE": "SPDR Real Estate",
    # Technology
    "SOXX": "iShares Semiconductors",
    "IGV":  "iShares Software",
    "SKYY": "First Trust Cloud Computing",
    "HACK": "ETFMG Cybersecurity",
    "PNQI": "Invesco Internet",
    "AIQ":  "Global X AI & Technology",
    "ROBO": "ROBO Global Robotics",
    "WCLD": "WisdomTree Cloud Computing",
    # Health Care
    "XBI":  "SPDR Biotech",
    "IBB":  "iShares Biotechnology",
    "IHI":  "iShares Medical Devices",
    "XPH":  "SPDR Pharmaceuticals",
    "ARKG": "ARK Genomic Revolution",
    "IHF":  "iShares Healthcare Providers",
    "IDNA": "iShares Genomics Immunology",
    # Financials
    "KRE":  "SPDR Regional Banking",
    "KBE":  "SPDR Banking",
    "IAK":  "iShares Insurance",
    "IAI":  "iShares Broker-Dealers",
    "KBWB": "Invesco Banking",
    "KBWR": "Invesco Regional Banking",
    "IPAY": "ETFMG Payments",
    # Energy
    "XOP":  "SPDR Oil & Gas E&P",
    "OIH":  "VanEck Oil Services",
    "TAN":  "Invesco Solar",
    "ICLN": "iShares Clean Energy",
    "AMLP": "Alerian MLP",
    "FCG":  "First Trust Natural Gas",
    # Industrials
    "ITA":  "iShares Aerospace & Defense",
    "XTN":  "SPDR Transportation",
    "JETS": "U.S. Global Jets",
    "ROAD": "Victory Road & Transport",
    "SAIA": "Saia Inc",
    # Consumer Discretionary
    "XRT":  "SPDR Retail",
    "ONLN": "ProShares Online Retail",
    "BETZ": "Roundhill Sports Betting",
    "GENZ": "Themes Generational Opp.",
    "CARZ": "First Trust Automobiles",
    # Consumer Staples
    "PBJ":  "Invesco Food & Beverage",
    "FTXG": "First Trust Food & Beverage",
    "VDC":  "Vanguard Consumer Staples",
    # Materials
    "GDX":  "VanEck Gold Miners",
    "SLX":  "VanEck Steel",
    "LIT":  "Global X Lithium & Battery",
    "COPX": "Global X Copper Miners",
    "PAVE": "Global X U.S. Infrastructure",
    "REMX": "VanEck Rare Earth/Strategic",
    # Communication
    "FIVG": "Defiance 5G Next Gen",
    "SOCL": "Global X Social Media",
    "NERD": "Roundhill Esports & Gaming",
    "ESPO": "VanEck Video Gaming & Esports",
    # Utilities
    "FUTY": "Fidelity Utilities",
    "UTES": "Virtus Reaves Utilities",
    "FAN":  "First Trust Wind Energy",
    "YLCO": "Global X Yieldco & Renewable",
    # Real Estate
    "VNQ":  "Vanguard Real Estate",
    "REZ":  "iShares Residential REIT",
    "SRVR": "Pacer Data & Infrastructure",
    "INDS": "Pacer Industrial REIT",
    "REM":  "iShares Mortgage Real Estate",
}

# ── Caché ────────────────────────────────────────────────────────
_cache      = {}
_cache_time = {}
CACHE_TTL   = 300   # 5 minutos


# ── Fórmula RS exacta de CDI (traducida desde PineScript) ────────
def _rs_score(close_ticker, close_spx):
    """
    Calcula el RS Score con la fórmula CDI:
      score = (0.4×Q1 + 0.2×Q2 + 0.2×Q3 + 0.2×Q4) /
              (0.4×SPX_Q1 + 0.2×SPX_Q2 + 0.2×SPX_Q3 + 0.2×SPX_Q4) × 100
    Q1=63d, Q2=126d, Q3=189d, Q4=252d
    """
    try:
        n = len(close_ticker)
        if n < 253:
            return None

        def perf(s, days):
            return float(s.iloc[-1]) / float(s.iloc[-1 - days])

        t63  = perf(close_ticker, 63)
        t126 = perf(close_ticker, 126)
        t189 = perf(close_ticker, 189)
        t252 = perf(close_ticker, 252)

        s63  = perf(close_spx, 63)
        s126 = perf(close_spx, 126)
        s189 = perf(close_spx, 189)
        s252 = perf(close_spx, 252)

        rs_stock = 0.4*t63 + 0.2*t126 + 0.2*t189 + 0.2*t252
        rs_ref   = 0.4*s63 + 0.2*s126 + 0.2*s189 + 0.2*s252

        return (rs_stock / rs_ref) * 100
    except Exception:
        return None


def _rs_rating(score, thresholds):
    """
    Convierte el RS Score a rating 1-99 usando interpolación lineal
    entre los 7 thresholds (igual que CDI/TradingView).
    thresholds = [first, scnd, thrd, frth, ffth, sxth, svth]  (descendente)
    """
    if score is None or thresholds is None:
        return None

    first, scnd, thrd, frth, ffth, sxth, svth = thresholds

    if score >= first:
        return 99
    if score <= svth:
        return 1

    def interpolate(score, taller, smaller, range_up, range_dn, weight):
        total = score + (score - smaller) * weight
        if total > taller - 1:
            total = taller - 1
        k1 = smaller / range_dn
        k2 = (taller - 1) / range_up
        k3 = (k1 - k2) / (taller - 1 - smaller)
        rating = total / (k1 - k3 * (score - smaller))
        return max(range_dn, min(range_up, rating))

    if score < first and score >= scnd:
        return round(interpolate(score, first, scnd, 98, 90, 0.33))
    if score < scnd  and score >= thrd:
        return round(interpolate(score, scnd,  thrd, 89, 70, 2.1))
    if score < thrd  and score >= frth:
        return round(interpolate(score, thrd,  frth, 69, 50, 0))
    if score < frth  and score >= ffth:
        return round(interpolate(score, frth,  ffth, 49, 30, 0))
    if score < ffth  and score >= sxth:
        return round(interpolate(score, ffth,  sxth, 29, 10, 0))
    if score < sxth  and score >= svth:
        return round(interpolate(score, sxth,  svth,  9,  2, 0))
    return None


def _build_thresholds(all_scores):
    """
    Genera los 7 thresholds desde el universo completo de ETFs.
    Equivalente al 'seed' de TradingView pero calculado con nuestro universo.
    Percentiles: 99, 90, 70, 50, 30, 10, 2
    """
    scores = sorted([s for s in all_scores if s is not None], reverse=True)
    if len(scores) < 7:
        return None
    n = len(scores)
    def pct_val(p):
        idx = int((1 - p/100) * n)
        return scores[min(idx, n-1)]
    return [
        pct_val(99),   # first
        pct_val(90),   # scnd
        pct_val(70),   # thrd
        pct_val(50),   # frth
        pct_val(30),   # ffth
        pct_val(10),   # sxth
        pct_val(2),    # svth
    ]


def _pct(series, periods):
    try:
        if len(series) <= periods:
            return None
        return round((float(series.iloc[-1]) / float(series.iloc[-periods]) - 1) * 100, 2)
    except Exception:
        return None


def _pct_ytd(series):
    try:
        tz  = series.index.tz
        ref = pd.Timestamp(datetime(datetime.today().year, 1, 1), tz=tz)
        ytd = series[series.index >= ref]
        if len(ytd) < 2:
            return None
        return round((float(ytd.iloc[-1]) / float(ytd.iloc[0]) - 1) * 100, 2)
    except Exception:
        return None


def get_sector_data(sector_key):
    """Descarga datos del sector y sus ETFs de sub-sector."""
    now = time.time()
    if sector_key in _cache and now - _cache_time.get(sector_key, 0) < CACHE_TTL:
        return _cache[sector_key]

    sector          = SECTORS[sector_key]
    display_tickers = [sector_key] + sector["components"]

    # Universo completo para calcular thresholds del RS
    all_etfs = ["^GSPC"] + list(set(
        [s for sec in SECTORS.values() for s in [list(SECTORS.keys())[list(SECTORS.values()).index(sec)]] + sec["components"]]
    ))

    try:
        tickers_to_dl = list(set(display_tickers + ["^GSPC"]))
        raw   = yf.download(tickers_to_dl, period="400d", progress=False, auto_adjust=True)
        close = raw["Close"]

        spx   = close["^GSPC"].dropna()

        # ── Paso 1: calcular RS Score de todos los ETFs del sector ──
        scores_map = {}
        for t in display_tickers:
            try:
                s = close[t].dropna()
                scores_map[t] = _rs_score(s, spx)
            except Exception:
                scores_map[t] = None

        thresholds = _build_thresholds(list(scores_map.values()))

        # ── Paso 2: construir filas ──────────────────────────────────
        rows = []
        for ticker in display_tickers:
            try:
                s = close[ticker].dropna()
                if s.empty:
                    continue
                price = round(float(s.iloc[-1]), 2)
                score = scores_map.get(ticker)
                rs    = _rs_rating(score, thresholds)

                rows.append({
                    "ticker": ticker,
                    "name":   NAMES.get(ticker, ticker),
                    "price":  price,
                    "rs":     rs,
                    "d1":     _pct(s, 1),
                    "w1":     _pct(s, 5),
                    "m1":     _pct(s, 21),
                    "ytd":    _pct_ytd(s),
                    "y1":     _pct(s, 252),
                })
            except Exception:
                continue

        _cache[sector_key]      = rows
        _cache_time[sector_key] = now
        return rows

    except Exception:
        return []
