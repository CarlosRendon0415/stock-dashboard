import yfinance as yf
import pandas as pd
import numpy as np

INDICES = {
    "SPX": "^GSPC",
    "NDX": "^NDX",
    "DJI": "^DJI",
    "RUT": "^RUT",
}


def get_market_data():
    results = {}

    tickers = list(INDICES.values())
    raw = yf.download(tickers, period="250d", progress=False, auto_adjust=True)

    if raw.empty:
        return results

    close_all = raw["Close"]

    for name, ticker in INDICES.items():
        try:
            close = close_all[ticker].dropna()

            if len(close) < 50:
                continue

            last_price = float(close.iloc[-1])

            dma5   = float(close.rolling(window=5).mean().iloc[-1])
            ema8   = float(close.ewm(span=8,   adjust=False).mean().iloc[-1])
            ema21  = float(close.ewm(span=21,  adjust=False).mean().iloc[-1])
            dma50  = float(close.rolling(window=50).mean().iloc[-1])
            dma200 = float(close.rolling(window=200).mean().iloc[-1])

            def pct(ma):
                return round(((last_price - ma) / ma) * 100, 2)

            results[name] = {
                "price": round(last_price, 2),
                "DMA5":  {"value": round(dma5,   2), "pct": pct(dma5)},
                "EMA8":  {"value": round(ema8,   2), "pct": pct(ema8)},
                "EMA21": {"value": round(ema21,  2), "pct": pct(ema21)},
                "DMA50": {"value": round(dma50,  2), "pct": pct(dma50)},
                "DMA200":{"value": round(dma200, 2), "pct": pct(dma200)},
            }

        except Exception:
            continue

    return results


def get_indicators_data():
    """
    Obtiene VIX, VVIX, SKEW y calcula Volatilidad Realizada (21d) del SPX.
    NYMO, Gamma GEX y Perfil de Volumen quedan pendientes a API de pago.
    """
    results = {}

    # ── VIX, VVIX, SKEW ─────────────────────────────────────────
    TICKERS = {
        "VIX":  "^VIX",
        "VVIX": "^VVIX",
        "SKEW": "^SKEW",
    }

    try:
        raw = yf.download(
            list(TICKERS.values()),
            period="30d",
            progress=False,
            auto_adjust=True,
        )
        close_all = raw["Close"]

        for name, ticker in TICKERS.items():
            try:
                series = close_all[ticker].dropna()
                if len(series) < 2:
                    continue
                last  = round(float(series.iloc[-1]), 2)
                prev  = round(float(series.iloc[-2]), 2)
                chg   = round(last - prev, 2)
                chg_p = round(((last - prev) / prev) * 100, 2)
                results[name] = {
                    "value": last,
                    "prev":  prev,
                    "chg":   chg,
                    "chg_p": chg_p,
                }
            except Exception:
                continue

    except Exception:
        pass

    # ── Volatilidad Realizada 21 días (SPX) ──────────────────────
    try:
        spx = yf.Ticker("^GSPC").history(period="60d")["Close"].dropna()
        if len(spx) >= 22:
            returns    = np.log(spx / spx.shift(1)).dropna()
            rv_21      = round(float(returns.iloc[-21:].std() * np.sqrt(252) * 100), 2)
            results["RV21"] = {
                "value": rv_21,
                "label": "Vol. Realizada 21d",
            }
    except Exception:
        pass

    return results
