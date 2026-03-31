import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from data import get_market_data, get_nymo_data

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


def semaphore_badge(pct):
    color = "#00C853" if pct > 0 else "#FF1744"
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
    # ── Encabezado ──────────────────────────────────────────────
    header = html.Thead(html.Tr([
        html.Th("Índice",   style={"width": "60px"}),
        html.Th("Nombre"),
        html.Th("Precio",   style={"text-align": "right"}),
        html.Th("DMA5",     style={"text-align": "center"}),
        html.Th("EMA8",     style={"text-align": "center"}),
        html.Th("EMA21",    style={"text-align": "center"}),
        html.Th("DMA50",    style={"text-align": "center"}),
        html.Th("DMA200",   style={"text-align": "center"}),
    ], style={"font-size": "12px", "color": "#888"}))

    # ── Filas ────────────────────────────────────────────────────
    rows = []
    for name, values in data.items():
        rows.append(html.Tr([
            html.Td(name,  style={"font-weight": "bold", "color": "#FFD600", "font-size": "13px"}),
            html.Td(INDEX_NAMES.get(name, ""), style={"color": "#AAAAAA", "font-size": "12px"}),
            html.Td(f"{values['price']:,.2f}", style={"text-align": "right", "color": "white", "font-size": "13px"}),
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


app.layout = dbc.Container([
    html.Div([
        html.H5("Semáforo de Mercado", className="text-white mb-1",
                style={"letter-spacing": "2px"}),
        html.P("Índices principales NYSE", className="text-secondary mb-0",
               style={"font-size": "12px"}),
    ], className="text-center mt-4 mb-3"),

    # Leyenda
    html.Div([
        html.Span("● Sobre la media", style={"color": "#00C853", "font-size": "12px", "margin-right": "16px"}),
        html.Span("● Bajo la media",  style={"color": "#FF1744", "font-size": "12px"}),
    ], className="text-center mb-3"),

    # Tabla índices
    html.Div(id="dashboard-content"),

    html.Hr(style={"border-color": "#333", "margin": "24px 0"}),

    # NYMO
    html.H6("McClellan Oscillator — NYMO", className="text-secondary text-center mb-3",
            style={"letter-spacing": "1px", "font-size": "12px"}),
    html.Div(id="nymo-content"),

    # Actualización cada 60 segundos
    dcc.Interval(id="interval", interval=60 * 1000, n_intervals=0),

    html.P("Datos con retraso de 15 min. Fuente: Yahoo Finance.",
           className="text-center text-secondary mt-3",
           style={"font-size": "11px"}),

], fluid=True, style={"background-color": "#0d0d1a", "min-height": "100vh", "padding": "20px"})


def build_nymo(nymo):
    if nymo is None:
        return html.P("No se pudieron obtener datos del NYMO.", style={"color": "#888", "font-size": "12px", "text-align": "center"})

    sign = "+" if nymo["nymo"] > 0 else ""

    return dbc.Row([
        # Valor principal
        dbc.Col(html.Div([
            html.Div(
                f"{sign}{nymo['nymo']}",
                style={
                    "font-size": "42px",
                    "font-weight": "bold",
                    "color": nymo["zone_color"],
                    "line-height": "1",
                }
            ),
            html.Span(
                nymo["zone"],
                style={
                    "background-color": nymo["zone_color"],
                    "color": "white",
                    "padding": "2px 10px",
                    "border-radius": "10px",
                    "font-size": "11px",
                    "font-weight": "bold",
                }
            ),
        ], className="text-center"), width=4),

        # Detalle
        dbc.Col(
            dbc.Table([
                html.Tbody([
                    html.Tr([html.Td("Net Advances",  style={"color": "#888", "font-size": "12px"}),
                             html.Td(f"{nymo['net']:,}", style={"color": "white", "font-size": "12px", "text-align": "right"})]),
                    html.Tr([html.Td("EMA 19",        style={"color": "#888", "font-size": "12px"}),
                             html.Td(f"{nymo['ema19']}", style={"color": "white", "font-size": "12px", "text-align": "right"})]),
                    html.Tr([html.Td("EMA 39",        style={"color": "#888", "font-size": "12px"}),
                             html.Td(f"{nymo['ema39']}", style={"color": "white", "font-size": "12px", "text-align": "right"})]),
                    html.Tr([html.Td("Sobrecompra",   style={"color": "#FF1744", "font-size": "11px"}),
                             html.Td("> +60",         style={"color": "#FF1744", "font-size": "11px", "text-align": "right"})]),
                    html.Tr([html.Td("Sobreventa",    style={"color": "#00C853", "font-size": "11px"}),
                             html.Td("< -60",         style={"color": "#00C853", "font-size": "11px", "text-align": "right"})]),
                ])
            ], bordered=False, size="sm"),
        width=8),
    ], className="justify-content-center align-items-center", style={"max-width": "500px", "margin": "0 auto"})


@app.callback(
    Output("dashboard-content", "children"),
    Output("nymo-content", "children"),
    Input("interval", "n_intervals"),
)
def update_dashboard(n):
    try:
        data = get_market_data()
        nymo = get_nymo_data()
        return build_table(data), build_nymo(nymo)
    except Exception as e:
        import traceback
        traceback.print_exc()
        error = html.P(f"Error al cargar datos: {str(e)}", style={"color": "red"})
        return error, error


if __name__ == "__main__":
    app.run(debug=False)
