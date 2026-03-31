import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from data import get_market_data, get_indicators_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Semáforo de Mercado"
server = app.server

MOVING_AVERAGES = ["DMA5", "EMA8", "EMA21", "DMA50", "DMA200"]

INDEX_NAMES = {
    "SPX": "S&P 500",
    "NDX": "Nasdaq 100",
    "DJI": "Dow Jones",
    "RUT": "Russell 2000",
}

# ── Colores semáforo ─────────────────────────────────────────────
COLOR_GREEN  = "#6B8E23"
COLOR_ORANGE = "#FF6D00"
COLOR_RED    = "#FF1744"
COLOR_GRAY   = "#555555"

TH_STYLE = {"color": "#888", "font-size": "11px", "border-bottom": "1px solid #333", "padding": "6px 10px"}
TD_STYLE = {"color": "#CCCCCC", "font-size": "12px", "padding": "6px 10px"}
TD_RIGHT = {**TD_STYLE, "text-align": "right"}


def semaphore_color(pct):
    if pct > 0.5:
        return COLOR_GREEN
    elif pct >= -0.5:
        return COLOR_ORANGE
    else:
        return COLOR_RED


def semaphore_badge(pct):
    color = semaphore_color(pct)
    sign  = "+" if pct > 0 else ""
    return html.Span(
        f"{sign}{pct}%",
        style={
            "background-color": color,
            "color": "white",
            "padding": "2px 8px",
            "border-radius": "10px",
            "font-size": "11px",
            "font-weight": "bold",
            "white-space": "nowrap",
        }
    )


def pending_badge():
    return html.Span("⏳ Pendiente", style={
        "background-color": "#333",
        "color": "#777",
        "padding": "2px 8px",
        "border-radius": "10px",
        "font-size": "11px",
        "font-weight": "bold",
    })


# ── Tabla izquierda: Índices ──────────────────────────────────────
def build_indices_table(data):
    header = html.Thead(html.Tr([
        html.Th("Índice",       style=TH_STYLE),
        html.Th("Nombre",       style=TH_STYLE),
        html.Th("Precio (USD)", style={**TH_STYLE, "text-align": "right"}),
        html.Th("DMA5",         style={**TH_STYLE, "text-align": "center"}),
        html.Th("EMA8",         style={**TH_STYLE, "text-align": "center"}),
        html.Th("EMA21",        style={**TH_STYLE, "text-align": "center"}),
        html.Th("DMA50",        style={**TH_STYLE, "text-align": "center"}),
        html.Th("DMA200",       style={**TH_STYLE, "text-align": "center"}),
    ]))

    rows = []
    for name, values in data.items():
        rows.append(html.Tr([
            html.Td(name, style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td(INDEX_NAMES.get(name, ""), style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(f"USD {values['price']:,.2f}", style=TD_RIGHT),
            *[html.Td(semaphore_badge(values[ma]["pct"]),
                      style={"text-align": "center", "padding": "5px 8px"})
              for ma in MOVING_AVERAGES],
        ]))

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=False, hover=True, size="sm",
        style={"font-size": "12px", "margin-bottom": "0"},
    )


# ── Tabla derecha: Indicadores ────────────────────────────────────
def vix_color(v):
    if v < 15:    return COLOR_GREEN
    elif v < 25:  return COLOR_ORANGE
    else:         return COLOR_RED

def vvix_color(v):
    if v < 90:    return COLOR_GREEN
    elif v < 110: return COLOR_ORANGE
    else:         return COLOR_RED

def skew_color(v):
    if v < 120:   return COLOR_GREEN
    elif v < 140: return COLOR_ORANGE
    else:         return COLOR_RED

def rv_color(v):
    if v < 12:    return COLOR_GREEN
    elif v < 20:  return COLOR_ORANGE
    else:         return COLOR_RED


def value_badge(value, color):
    return html.Span(
        f"{value}",
        style={
            "background-color": color,
            "color": "white",
            "padding": "2px 8px",
            "border-radius": "10px",
            "font-size": "11px",
            "font-weight": "bold",
            "white-space": "nowrap",
        }
    )


def build_indicators_table(ind):
    rows = []

    # ── NYMO ────────────────────────────────────────────────────
    rows.append(html.Tr([
        html.Td("NYMO",             style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
        html.Td("McClellan Osc.",   style={**TD_STYLE, "color": "#AAAAAA"}),
        html.Td(pending_badge(),    style={"text-align": "center", "padding": "5px 8px"}),
        html.Td("—",                style={**TD_RIGHT, "color": "#555"}),
    ]))

    # ── VIX ─────────────────────────────────────────────────────
    if "VIX" in ind:
        v = ind["VIX"]
        sign = "+" if v["chg"] > 0 else ""
        rows.append(html.Tr([
            html.Td("VIX",                   style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Volatilidad implícita",  style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(value_badge(v["value"], vix_color(v["value"])),
                    style={"text-align": "center", "padding": "5px 8px"}),
            html.Td(f"{sign}{v['chg_p']}%",  style={**TD_RIGHT, "color": COLOR_RED if v["chg"] > 0 else COLOR_GREEN}),
        ]))
    else:
        rows.append(html.Tr([
            html.Td("VIX",  style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Volatilidad implícita", style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(pending_badge(), style={"text-align": "center", "padding": "5px 8px"}),
            html.Td("—", style={**TD_RIGHT, "color": "#555"}),
        ]))

    # ── VVIX ────────────────────────────────────────────────────
    if "VVIX" in ind:
        v = ind["VVIX"]
        sign = "+" if v["chg"] > 0 else ""
        rows.append(html.Tr([
            html.Td("VVIX",                  style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Vol. del VIX",          style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(value_badge(v["value"], vvix_color(v["value"])),
                    style={"text-align": "center", "padding": "5px 8px"}),
            html.Td(f"{sign}{v['chg_p']}%",  style={**TD_RIGHT, "color": COLOR_RED if v["chg"] > 0 else COLOR_GREEN}),
        ]))
    else:
        rows.append(html.Tr([
            html.Td("VVIX", style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Vol. del VIX", style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(pending_badge(), style={"text-align": "center", "padding": "5px 8px"}),
            html.Td("—", style={**TD_RIGHT, "color": "#555"}),
        ]))

    # ── SKEW ────────────────────────────────────────────────────
    if "SKEW" in ind:
        v = ind["SKEW"]
        sign = "+" if v["chg"] > 0 else ""
        rows.append(html.Tr([
            html.Td("SKEW",              style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Riesgo de cola",    style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(value_badge(v["value"], skew_color(v["value"])),
                    style={"text-align": "center", "padding": "5px 8px"}),
            html.Td(f"{sign}{v['chg_p']}%", style={**TD_RIGHT, "color": COLOR_RED if v["chg"] > 0 else COLOR_GREEN}),
        ]))
    else:
        rows.append(html.Tr([
            html.Td("SKEW", style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Riesgo de cola", style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(pending_badge(), style={"text-align": "center", "padding": "5px 8px"}),
            html.Td("—", style={**TD_RIGHT, "color": "#555"}),
        ]))

    # ── Vol. Realizada 21d ───────────────────────────────────────
    if "RV21" in ind:
        v = ind["RV21"]["value"]
        rows.append(html.Tr([
            html.Td("RV 21d",            style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Vol. Realizada 21d", style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(value_badge(f"{v}%", rv_color(v)),
                    style={"text-align": "center", "padding": "5px 8px"}),
            html.Td("SPX",               style={**TD_RIGHT, "color": "#555"}),
        ]))
    else:
        rows.append(html.Tr([
            html.Td("RV 21d", style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
            html.Td("Vol. Realizada 21d", style={**TD_STYLE, "color": "#AAAAAA"}),
            html.Td(pending_badge(), style={"text-align": "center", "padding": "5px 8px"}),
            html.Td("—", style={**TD_RIGHT, "color": "#555"}),
        ]))

    # ── Gamma GEX ───────────────────────────────────────────────
    rows.append(html.Tr([
        html.Td("GEX",              style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
        html.Td("Gamma Exposure",   style={**TD_STYLE, "color": "#AAAAAA"}),
        html.Td(pending_badge(),    style={"text-align": "center", "padding": "5px 8px"}),
        html.Td("—",                style={**TD_RIGHT, "color": "#555"}),
    ]))

    # ── Perfil de Volumen ────────────────────────────────────────
    rows.append(html.Tr([
        html.Td("VPVR",                       style={**TD_STYLE, "font-weight": "bold", "color": "#FFD600"}),
        html.Td("Perfil Vol. Rango Visible",  style={**TD_STYLE, "color": "#AAAAAA"}),
        html.Td(pending_badge(),              style={"text-align": "center", "padding": "5px 8px"}),
        html.Td("—",                          style={**TD_RIGHT, "color": "#555"}),
    ]))

    header = html.Thead(html.Tr([
        html.Th("Ticker",       style=TH_STYLE),
        html.Th("Indicador",    style=TH_STYLE),
        html.Th("Valor",        style={**TH_STYLE, "text-align": "center"}),
        html.Th("Cambio",       style={**TH_STYLE, "text-align": "right"}),
    ]))

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=False, hover=True, size="sm",
        style={"font-size": "12px", "margin-bottom": "0"},
    )


# ── Layout ────────────────────────────────────────────────────────
app.layout = dbc.Container([

    # Título
    html.Div([
        html.H5("Semáforo de Mercado", className="text-white mb-1",
                style={"letter-spacing": "2px"}),
        html.P("Índices principales NYSE · Indicadores de Mercado",
               className="text-secondary mb-0", style={"font-size": "12px"}),
    ], className="text-center mt-4 mb-3"),

    # Leyenda
    html.Div([
        html.Span("● > +0.5%",       style={"color": COLOR_GREEN,  "font-size": "12px", "margin-right": "14px"}),
        html.Span("● -0.5% a +0.5%", style={"color": COLOR_ORANGE, "font-size": "12px", "margin-right": "14px"}),
        html.Span("● < -0.5%",       style={"color": COLOR_RED,    "font-size": "12px"}),
    ], className="text-center mb-4"),

    # ── Layout 50 / 50 ──────────────────────────────────────────
    dbc.Row([

        # Columna izquierda — Índices (50%)
        dbc.Col([
            html.H6("Índices del Mercado", className="text-secondary mb-2",
                    style={"font-size": "11px", "letter-spacing": "1px", "text-transform": "uppercase"}),
            html.Div(id="indices-content"),
        ], xs=12, lg=6, className="pe-lg-3"),

        # Columna derecha — Indicadores (50%)
        dbc.Col([
            html.H6("Indicadores de Sentimiento", className="text-secondary mb-2",
                    style={"font-size": "11px", "letter-spacing": "1px", "text-transform": "uppercase"}),
            html.Div(id="indicators-content"),
        ], xs=12, lg=6, className="ps-lg-3"),

    ], className="g-0"),

    # Actualización cada 60 segundos
    dcc.Interval(id="interval", interval=60 * 1000, n_intervals=0),

    html.P("Datos con retraso de 15 min. Fuente: Yahoo Finance.",
           className="text-center text-secondary mt-4",
           style={"font-size": "11px"}),

], fluid=True, style={"background-color": "#0d0d1a", "min-height": "100vh", "padding": "20px"})


@app.callback(
    Output("indices-content",    "children"),
    Output("indicators-content", "children"),
    Input("interval", "n_intervals"),
)
def update_dashboard(n):
    try:
        market = get_market_data()
        ind    = get_indicators_data()
        return build_indices_table(market), build_indicators_table(ind)
    except Exception as e:
        import traceback
        traceback.print_exc()
        err = html.P(f"Error: {str(e)}", style={"color": "red", "font-size": "12px"})
        return err, err


if __name__ == "__main__":
    app.run(debug=False)
