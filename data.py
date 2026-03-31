import yfinance as yf

INDICES = {
    "SPX": "^GSPC",
    "NDX": "^NDX",
    "DJI": "^DJI",
    "RUT": "^RUT",
}


def get_market_data():
    results = {}

    # Una sola llamada para todos los índices (evita rate limiting)
    tickers = list(INDICES.values())
    raw = yf.download(tickers, period="250d", progress=False, auto_adjust=True)

    if raw.empty:
        return results

    close_all = raw["Close"]

    for name, ticker in INDICES.items():
        try:
            close = close_all[ticker].dropna()

            if len(close) < 200:
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
