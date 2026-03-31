import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from data import get_market_data, get_indicators_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "CDI · Semáforo de Mercado"
server = app.server

MOVING_AVERAGES = ["DMA5", "EMA8", "EMA21", "DMA50", "DMA200"]

INDEX_NAMES = {
    "SPX": "S&P 500",
    "NDX": "Nasdaq 100",
    "DJI": "Dow Jones",
    "RUT": "Russell 2000",
}

# ── Paleta CDI ────────────────────────────────────────────────────
CDI_MINT  = "#00E5A0"
CDI_NAVY  = "#0D1B3E"
CDI_NAVY2 = "#162447"
CDI_WHITE = "#FFFFFF"
CDI_GRAY  = "#8892A4"

SEM_GREEN  = "#6B8E23"
SEM_ORANGE = "#FF6D00"
SEM_RED    = "#FF1744"

TH = {
    "color": CDI_MINT, "font-size": "11px", "font-weight": "700",
    "letter-spacing": "1px", "text-transform": "uppercase",
    "padding": "8px 10px", "border-bottom": f"2px solid {CDI_MINT}",
    "background-color": CDI_NAVY, "white-space": "nowrap",
}
TD       = {"color": CDI_WHITE, "font-size": "12px", "padding": "7px 10px",
            "border-bottom": "1px solid #1E2D4F", "white-space": "nowrap"}
TD_MUTED = {**TD, "color": CDI_GRAY}
TD_RIGHT = {**TD, "text-align": "right"}


# ── Contenido pedagógico de tooltips ─────────────────────────────
# Reemplaza los href="#" con las URLs reales de tus videos en Thinkific
TOOLTIPS = {
    "DMA5": {
        "desc": "Media Móvil Simple de 5 días. Promedio del precio de cierre de las últimas 5 sesiones. Muy sensible a movimientos de corto plazo.",
        "url":  "#",
    },
    "EMA8": {
        "desc": "Media Móvil Exponencial de 8 períodos. Da mayor peso a los precios recientes. Ideal para detectar tendencias de corto plazo.",
        "url":  "#",
    },
    "EMA21": {
        "desc": "Media Móvil Exponencial de 21 períodos. Referencia de tendencia de mediano plazo. Ampliamente utilizada por traders institucionales.",
        "url":  "#",
    },
    "DMA50": {
        "desc": "Media Móvil Simple de 50 días. Indicador clave de tendencia intermedia. El precio sobre la DMA50 es señal de fortaleza.",
        "url":  "#",
    },
    "DMA200": {
        "desc": "Media Móvil Simple de 200 días. La más importante a largo plazo. Precio sobre DMA200 = tendencia alcista. Precio bajo = tendencia bajista.",
        "url":  "#",
    },
    "NYMO": {
        "desc": "Oscilador de McClellan. Mide la amplitud del mercado usando la diferencia entre acciones que suben y bajan en el NYSE. Sobre +60: sobrecompra. Bajo -60: sobreventa.",
        "url":  "#",
    },
    "VIX": {
        "desc": "Índice del miedo del CBOE. Refleja la volatilidad implícita esperada del S&P 500 a 30 días. VIX < 15: calma. Entre 15-25: precaución. VIX > 25: miedo extremo.",
        "url":  "#",
    },
    "VVIX": {
        "desc": "Volatilidad del VIX. Mide qué tan rápido puede cambiar el propio VIX. Valores altos anticipan cambios abruptos en el sentimiento del mercado.",
        "url":  "#",
    },
    "SKEW": {
        "desc": "Índice de riesgo de cola del CBOE. Mide cuánto paga el mercado por protección ante caídas extremas. SKEW > 140: el mercado anticipa eventos de cola (cisnes negros).",
        "url":  "#",
    },
    "RV21": {
        "desc": "Volatilidad Realizada en 21 días hábiles (~1 mes). Mide el movimiento real del SPX. Comparar RV vs VIX indica si el mercado sobreestima o subestima la volatilidad.",
        "url":  "#",
    },
    "GEX": {
        "desc": "Gamma Exposure de los market makers en opciones del S&P 500. GEX positivo amortigua movimientos del mercado. GEX negativo los amplifica.",
        "url":  "#",
    },
    "VPVR": {
        "desc": "Perfil de Volumen del Rango Visible. Muestra el volumen en cada nivel de precio dentro del rango del gráfico. Identifica soportes y resistencias por volumen real.",
        "url":  "#",
    },
}


def info_icon(key):
    """Ícono ℹ con tooltip CSS puro — funciona con contenido dinámico."""
    t = TOOLTIPS.get(key, {})
    return html.Span([
        html.Span("ℹ", className="cdi-tip-icon"),
        html.Div([
            html.P(t.get("desc", ""), className="cdi-tip-desc"),
            html.A("Ver video explicativo →",
                   href=t.get("url", "#"),
                   target="_blank",
                   className="cdi-tip-link"),
        ], className="cdi-tip-box"),
    ], className="cdi-tip-wrap")


# ── Helpers ──────────────────────────────────────────────────────
def sem_color(pct):
    if pct > 0.5:   return SEM_GREEN
    if pct >= -0.5: return SEM_ORANGE
    return SEM_RED


def badge(text, bg, text_color=CDI_WHITE):
    return html.Span(text, style={
        "background-color": bg, "color": text_color,
        "padding": "3px 9px", "border-radius": "20px",
        "font-size": "11px", "font-weight": "700", "white-space": "nowrap",
    })


def pending_badge():
    return badge("⏳ Pendiente", "#1E2D4F", CDI_GRAY)


def vix_color(v):
    return SEM_GREEN if v < 15 else (SEM_ORANGE if v < 25 else SEM_RED)

def vvix_color(v):
    return SEM_GREEN if v < 90 else (SEM_ORANGE if v < 110 else SEM_RED)

def skew_color(v):
    return SEM_GREEN if v < 120 else (SEM_ORANGE if v < 140 else SEM_RED)

def rv_color(v):
    return SEM_GREEN if v < 12 else (SEM_ORANGE if v < 20 else SEM_RED)


# ── Tabla de Índices ─────────────────────────────────────────────
def build_indices_table(data):
    def ma_th(ma):
        return html.Th(
            html.Span([ma, info_icon(f"info-{ma}")]),
            style={**TH, "text-align": "center"}
        )

    header = html.Thead(html.Tr([
        html.Th("Índice",       style=TH),
        html.Th("Nombre",       style=TH),
        html.Th("Precio (USD)", style={**TH, "text-align": "right"}),
        *[ma_th(ma) for ma in MOVING_AVERAGES],
    ]))

    rows = []
    for i, (name, values) in enumerate(data.items()):
        bg = CDI_NAVY if i % 2 == 0 else CDI_NAVY2
        rows.append(html.Tr([
            html.Td(name, style={**TD, "background-color": bg,
                                 "color": CDI_MINT, "font-weight": "700"}),
            html.Td(INDEX_NAMES.get(name, ""), style={**TD_MUTED, "background-color": bg}),
            html.Td(f"USD {values['price']:,.2f}",
                    style={**TD_RIGHT, "background-color": bg, "font-weight": "600"}),
            *[html.Td(
                badge(("+" if values[ma]["pct"] > 0 else "") + f"{values[ma]['pct']}%",
                      sem_color(values[ma]["pct"])),
                style={"text-align": "center", "padding": "6px 8px",
                       "background-color": bg, "border-bottom": "1px solid #1E2D4F"}
            ) for ma in MOVING_AVERAGES],
        ]))

    return html.Div([
        dbc.Table(
            [header, html.Tbody(rows)],
            bordered=False, hover=False, size="sm",
            style={"margin-bottom": "0", "border-collapse": "collapse"},
        )
    ], style={"border-radius": "12px",
              "border": f"1px solid {CDI_MINT}33"})


# ── Tarjetas de Indicadores ──────────────────────────────────────
def indicator_card(key, ticker, label, value_node, change_node=None):
    return html.Div([
        html.Div([
            html.Span(ticker, style={
                "color": CDI_MINT, "font-weight": "700",
                "font-size": "14px", "letter-spacing": "1px",
            }),
            info_icon(f"info-{key}"),
            html.Span(label, style={
                "color": CDI_GRAY, "font-size": "11px", "margin-left": "8px",
            }),
        ], style={"margin-bottom": "10px"}),
        html.Div([
            value_node,
            html.Span(change_node or "", style={"margin-left": "8px"}),
        ], style={"display": "flex", "align-items": "center"}),
    ], style={
        "background-color": CDI_NAVY2,
        "border": f"1px solid {CDI_MINT}33",
        "border-radius": "12px",
        "padding": "14px 16px",
        "height": "100%",
    })


def build_indicators_cards(ind):
    def chg_span(chg, chg_p):
        sign  = "+" if chg > 0 else ""
        color = SEM_RED if chg > 0 else SEM_GREEN
        return html.Span(f"{sign}{chg_p}%",
                         style={"color": color, "font-size": "11px", "font-weight": "600"})

    nymo_card = indicator_card("NYMO", "NYMO", "McClellan Osc.", pending_badge())

    if "VIX" in ind:
        v = ind["VIX"]
        vix_card = indicator_card("VIX", "VIX", "Volatilidad implícita",
                                  badge(str(v["value"]), vix_color(v["value"])),
                                  chg_span(v["chg"], v["chg_p"]))
    else:
        vix_card = indicator_card("VIX", "VIX", "Volatilidad implícita", pending_badge())

    if "VVIX" in ind:
        v = ind["VVIX"]
        vvix_card = indicator_card("VVIX", "VVIX", "Vol. del VIX",
                                   badge(str(v["value"]), vvix_color(v["value"])),
                                   chg_span(v["chg"], v["chg_p"]))
    else:
        vvix_card = indicator_card("VVIX", "VVIX", "Vol. del VIX", pending_badge())

    if "SKEW" in ind:
        v = ind["SKEW"]
        skew_card = indicator_card("SKEW", "SKEW", "Riesgo de cola",
                                   badge(str(v["value"]), skew_color(v["value"])),
                                   chg_span(v["chg"], v["chg_p"]))
    else:
        skew_card = indicator_card("SKEW", "SKEW", "Riesgo de cola", pending_badge())

    if "RV21" in ind:
        v = ind["RV21"]["value"]
        rv_card = indicator_card("RV21", "RV 21d", "Vol. Realizada SPX",
                                 badge(f"{v}%", rv_color(v)))
    else:
        rv_card = indicator_card("RV21", "RV 21d", "Vol. Realizada SPX", pending_badge())

    gex_card  = indicator_card("GEX",  "GEX",  "Gamma Exposure",           pending_badge())
    vpvr_card = indicator_card("VPVR", "VPVR", "Perfil Vol. Rango Visible", pending_badge())

    return html.Div([
        dbc.Row([dbc.Col(nymo_card, xs=6, className="mb-3"),
                 dbc.Col(vix_card,  xs=6, className="mb-3")], className="g-2"),
        dbc.Row([dbc.Col(vvix_card, xs=6, className="mb-3"),
                 dbc.Col(skew_card, xs=6, className="mb-3")], className="g-2"),
        dbc.Row([dbc.Col(rv_card,   xs=6, className="mb-3"),
                 dbc.Col(gex_card,  xs=6, className="mb-3")], className="g-2"),
        dbc.Row([dbc.Col(vpvr_card, xs=12, className="mb-3")], className="g-2"),
    ])




# ── Layout ────────────────────────────────────────────────────────
app.layout = html.Div([
    dbc.Container([

        html.Div([
            html.Div([
                html.Span("CLUB DE INVERSIONISTAS", style={
                    "color": CDI_MINT, "font-size": "26px",
                    "font-weight": "900", "letter-spacing": "3px",
                }),
            ], style={"margin-bottom": "4px"}),
            html.P("Semáforo de Mercado · NYSE", style={
                "color": CDI_GRAY, "font-size": "12px",
                "margin": "0", "letter-spacing": "2px",
            }),
        ], className="text-center py-4"),

        html.Div([
            html.Span("● > +0.5%",       style={"color": SEM_GREEN,  "font-size": "12px", "margin-right": "16px"}),
            html.Span("● -0.5% a +0.5%", style={"color": SEM_ORANGE, "font-size": "12px", "margin-right": "16px"}),
            html.Span("● < -0.5%",       style={"color": SEM_RED,    "font-size": "12px"}),
        ], className="text-center mb-4"),

        dbc.Row([
            dbc.Col([
                html.P("ÍNDICES DEL MERCADO", style={
                    "color": CDI_MINT, "font-size": "11px",
                    "font-weight": "700", "letter-spacing": "2px", "margin-bottom": "10px",
                }),
                html.Div(id="indices-content"),
            ], xs=12, lg=6, className="pe-lg-3 mb-4"),

            dbc.Col([
                html.P("INDICADORES DE SENTIMIENTO", style={
                    "color": CDI_MINT, "font-size": "11px",
                    "font-weight": "700", "letter-spacing": "2px", "margin-bottom": "10px",
                }),
                html.Div(id="indicators-content"),
            ], xs=12, lg=6, className="ps-lg-3 mb-4"),
        ]),

        html.P("Datos con retraso de 15 min. Fuente: Yahoo Finance.",
               className="text-center mt-2 pb-4",
               style={"color": CDI_GRAY, "font-size": "11px"}),

        dcc.Interval(id="interval", interval=60 * 1000, n_intervals=0),

    ], fluid=True),
], style={"background-color": CDI_NAVY, "min-height": "100vh",
          "font-family": "'Segoe UI', sans-serif"})


@app.callback(
    Output("indices-content",    "children"),
    Output("indicators-content", "children"),
    Input("interval", "n_intervals"),
)
def update_dashboard(n):
    try:
        market = get_market_data()
        ind    = get_indicators_data()
        return build_indices_table(market), build_indicators_cards(ind)
    except Exception as e:
        import traceback
        traceback.print_exc()
        err = html.P(f"Error: {str(e)}", style={"color": SEM_RED, "font-size": "12px"})
        return err, err


if __name__ == "__main__":
    app.run(debug=False)
