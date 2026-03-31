import yfinance as yf
import pandas as pd

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


def get_nymo_data():
    """
    Calcula el McClellan Oscillator (NYMO) con la fórmula oficial:
      Net Advances  = diferencia diaria de ^NYAD (NYSE Advance-Decline Line)
      EMA19 = EMA(Net Advances, span=19)
      EMA39 = EMA(Net Advances, span=39)
      NYMO  = EMA19 - EMA39
    """
    try:
        nyad = yf.Ticker("^NYAD").history(period="150d")["Close"].dropna()

        if len(nyad) < 42:
            return None

        # La diferencia diaria del acumulado = Net Advances del día
        net_advances = nyad.diff().dropna()

        df = pd.DataFrame({"net": net_advances}).dropna()
        df["ema19"] = df["net"].ewm(span=19, adjust=False).mean()
        df["ema39"] = df["net"].ewm(span=39, adjust=False).mean()
        df["nymo"]  = df["ema19"] - df["ema39"]

        nymo_value  = round(float(df["nymo"].iloc[-1]),  2)
        ema19_value = round(float(df["ema19"].iloc[-1]), 2)
        ema39_value = round(float(df["ema39"].iloc[-1]), 2)
        net_value   = round(float(df["net"].iloc[-1]),   0)

        if nymo_value >= 60:
            zone       = "Sobrecompra"
            zone_color = "#FF1744"
        elif nymo_value <= -60:
            zone       = "Sobreventa"
            zone_color = "#00C853"
        else:
            zone       = "Neutral"
            zone_color = "#FFD600"

        return {
            "nymo":       nymo_value,
            "ema19":      ema19_value,
            "ema39":      ema39_value,
            "net":        int(net_value),
            "zone":       zone,
            "zone_color": zone_color,
        }

    except Exception:
        return None
