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

    # Tabla
    html.Div(id="dashboard-content"),

    # Actualización cada 60 segundos
    dcc.Interval(id="interval", interval=60 * 1000, n_intervals=0),

    html.P("Datos con retraso de 15 min. Fuente: Yahoo Finance.",
           className="text-center text-secondary mt-3",
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
