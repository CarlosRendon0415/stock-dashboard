import yfinance as yf

INDICES = {
    "SPX": "^GSPC",
    "NDX": "^NDX",
    "DJI": "^DJI",
    "RUT": "^RUT",
}


def get_market_data():
    results = {}

    for name, ticker in INDICES.items():
        raw = yf.Ticker(ticker).history(period="250d")

        if raw.empty:
            continue

        close = raw["Close"].dropna()
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

    return results
