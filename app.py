import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from data import get_market_data

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
COLOR_GREEN  = "#6B8E23"   # verde oliva  → > +0.5%
COLOR_ORANGE = "#FF6D00"   # naranja      → entre -0.5% y +0.5%
COLOR_RED    = "#FF1744"   # rojo         → < -0.5%


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
            "font-size": "12px",
            "font-weight": "bold",
            "white-space": "nowrap",
        }
    )


def build_table(data):
    header = html.Thead(html.Tr([
        html.Th("Índice",  style={"width": "60px"}),
        html.Th("Nombre"),
        html.Th("Precio (USD)", style={"text-align": "right"}),
        html.Th("DMA5",    style={"text-align": "center"}),
        html.Th("EMA8",    style={"text-align": "center"}),
        html.Th("EMA21",   style={"text-align": "center"}),
        html.Th("DMA50",   style={"text-align": "center"}),
        html.Th("DMA200",  style={"text-align": "center"}),
    ], style={"font-size": "12px", "color": "#888"}))

    rows = []
    for name, values in data.items():
        rows.append(html.Tr([
            html.Td(name, style={"font-weight": "bold", "color": "#FFD600", "font-size": "13px"}),
            html.Td(INDEX_NAMES.get(name, ""), style={"color": "#AAAAAA", "font-size": "12px"}),
            html.Td(
                f"USD {values['price']:,.2f}",
                style={"text-align": "right", "color": "white", "font-size": "13px"}
            ),
            *[html.Td(semaphore_badge(values[ma]["pct"]),
                      style={"text-align": "center", "padding": "6px 8px"})
              for ma in MOVING_AVERAGES],
        ]))

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=False,
        hover=True,
        size="sm",
        style={"font-size": "13px"},
    )


def build_nymo_pending():
    """Sección NYMO temporal mientras se integra la API de pago."""
    return dbc.Row([

        # ── Semáforo (izquierda) ─────────────────────────────────
        dbc.Col(
            html.Div([
                html.Div("—", style={
                    "font-size": "48px",
                    "font-weight": "bold",
                    "color": "#555",
                    "line-height": "1",
                }),
                html.Span("Pendiente", style={
                    "background-color": "#444",
                    "color": "#aaa",
                    "padding": "2px 10px",
                    "border-radius": "10px",
                    "font-size": "11px",
                    "font-weight": "bold",
                    "display": "inline-block",
                    "margin-top": "6px",
                }),
            ], className="text-center"),
            xs=12, sm=4,
        ),

        # ── Tabla de detalle (derecha) ───────────────────────────
        dbc.Col(
            dbc.Table([
                html.Tbody([
                    html.Tr([
                        html.Td("NYMO",         style={"color": "#888", "font-size": "12px"}),
                        html.Td("—",            style={"color": "#555", "font-size": "12px", "text-align": "right"}),
                    ]),
                    html.Tr([
                        html.Td("Net Advances", style={"color": "#888", "font-size": "12px"}),
                        html.Td("—",            style={"color": "#555", "font-size": "12px", "text-align": "right"}),
                    ]),
                    html.Tr([
                        html.Td("EMA 19",       style={"color": "#888", "font-size": "12px"}),
                        html.Td("—",            style={"color": "#555", "font-size": "12px", "text-align": "right"}),
                    ]),
                    html.Tr([
                        html.Td("EMA 39",       style={"color": "#888", "font-size": "12px"}),
                        html.Td("—",            style={"color": "#555", "font-size": "12px", "text-align": "right"}),
                    ]),
                    html.Tr([
                        html.Td("Sobrecompra",  style={"color": COLOR_RED,   "font-size": "11px"}),
                        html.Td("> +60",        style={"color": COLOR_RED,   "font-size": "11px", "text-align": "right"}),
                    ]),
                    html.Tr([
                        html.Td("Sobreventa",   style={"color": COLOR_GREEN, "font-size": "11px"}),
                        html.Td("< -60",        style={"color": COLOR_GREEN, "font-size": "11px", "text-align": "right"}),
                    ]),
                ])
            ], bordered=False, size="sm"),
            xs=12, sm=8,
        ),

    ], className="align-items-center", style={"max-width": "480px", "margin": "0 auto"})


# ── Layout ────────────────────────────────────────────────────────
app.layout = dbc.Container([

    html.Div([
        html.H5("Semáforo de Mercado", className="text-white mb-1",
                style={"letter-spacing": "2px"}),
        html.P("Índices principales NYSE", className="text-secondary mb-0",
               style={"font-size": "12px"}),
    ], className="text-center mt-4 mb-3"),

    # Leyenda semáforo
    html.Div([
        html.Span("● > +0.5%",            style={"color": COLOR_GREEN,  "font-size": "12px", "margin-right": "14px"}),
        html.Span("● -0.5% a +0.5%",      style={"color": COLOR_ORANGE, "font-size": "12px", "margin-right": "14px"}),
        html.Span("● < -0.5%",            style={"color": COLOR_RED,    "font-size": "12px"}),
    ], className="text-center mb-3"),

    # Tabla índices
    html.Div(id="dashboard-content"),

    html.Hr(style={"border-color": "#333", "margin": "24px 0"}),

    # NYMO
    html.H6("McClellan Oscillator — NYMO", className="text-secondary text-center mb-3",
            style={"letter-spacing": "1px", "font-size": "12px"}),

    # Recuadro "Pendiente"
    html.Div(
        html.Div([
            html.P("⏳ Pendiente a la API de pago",
                   style={"color": "#888", "font-size": "13px", "margin": "0"}),
        ], style={
            "border": "1px dashed #444",
            "border-radius": "8px",
            "padding": "12px 20px",
            "display": "inline-block",
        }),
        className="text-center mb-3",
    ),

    build_nymo_pending(),

    # Actualización cada 60 segundos
    dcc.Interval(id="interval", interval=60 * 1000, n_intervals=0),

    html.P("Datos con retraso de 15 min. Fuente: Yahoo Finance.",
           className="text-center text-secondary mt-4",
           style={"font-size": "11px"}),

], fluid=True, style={"background-color": "#0d0d1a", "min-height": "100vh", "padding": "20px"})


@app.callback(
    Output("dashboard-content", "children"),
    Input("interval", "n_intervals"),
)
def update_dashboard(n):
    try:
        data = get_market_data()
        return build_table(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.P(f"Error al cargar datos: {str(e)}", style={"color": "red"})


if __name__ == "__main__":
    app.run(debug=False)
