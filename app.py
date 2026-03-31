import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from data import get_market_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Semáforo de Mercado"
server = app.server   # necesario para gunicorn en producción

MOVING_AVERAGES = ["DMA5", "EMA8", "EMA21", "DMA50", "DMA200"]


def semaphore_color(pct):
    """Verde = precio sobre la media | Rojo = precio bajo la media"""
    if pct > 0:
        return "#00C853"   # verde
    elif pct < 0:
        return "#FF1744"   # rojo
    return "#FFD600"       # amarillo (exactamente en la media)


def make_index_card(name, data):
    rows = []
    for ma in MOVING_AVERAGES:
        pct = data[ma]["pct"]
        color = semaphore_color(pct)
        sign = "+" if pct > 0 else ""

        rows.append(
            html.Tr([
                html.Td(ma, style={"color": "#CCCCCC", "padding": "8px 12px", "font-weight": "600"}),
                html.Td(
                    f"{data[ma]['value']:,.2f}",
                    style={"color": "#AAAAAA", "padding": "8px 12px", "text-align": "right"}
                ),
                html.Td(
                    html.Span(
                        f"{sign}{pct}%",
                        style={
                            "background-color": color,
                            "color": "white",
                            "padding": "3px 10px",
                            "border-radius": "12px",
                            "font-weight": "bold",
                            "display": "inline-block",
                            "min-width": "75px",
                            "text-align": "center",
                            "font-size": "13px",
                        }
                    ),
                    style={"padding": "8px 12px", "text-align": "center"}
                ),
            ])
        )

    return dbc.Card([
        dbc.CardHeader(
            html.H4(name, className="text-center text-white mb-0",
                    style={"letter-spacing": "2px"})
        ),
        dbc.CardBody([
            html.H5(
                f"Último cierre: {data['price']:,.2f}",
                className="text-center text-warning mb-3"
            ),
            dbc.Table(
                [
                    html.Thead(html.Tr([
                        html.Th("Media",    style={"color": "#888", "font-size": "12px"}),
                        html.Th("Valor",    style={"color": "#888", "font-size": "12px", "text-align": "right"}),
                        html.Th("% vs Precio", style={"color": "#888", "font-size": "12px", "text-align": "center"}),
                    ])),
                    html.Tbody(rows),
                ],
                bordered=False,
                hover=True,
                size="sm",
            ),
        ]),
    ], color="dark", outline=True, className="h-100")


app.layout = dbc.Container([
    # ── Encabezado ──────────────────────────────────────────────
    html.Div([
        html.H2("Semáforo de Mercado", className="text-white mb-1",
                style={"letter-spacing": "3px"}),
        html.P("Índices principles NYSE · DMA5 · EMA8 · EMA21 · DMA50 · DMA200",
               className="text-secondary mb-0", style={"font-size": "13px"}),
    ], className="text-center my-4"),

    # ── Leyenda de colores ───────────────────────────────────────
    dbc.Row([
        dbc.Col(
            html.Div([
                html.Span("● Precio sobre la media", style={"color": "#00C853", "font-size": "13px", "margin-right": "20px"}),
                html.Span("● Precio bajo la media",  style={"color": "#FF1744", "font-size": "13px"}),
            ]),
            className="text-center mb-4"
        )
    ]),

    # ── Tarjetas de índices ──────────────────────────────────────
    html.Div(id="dashboard-content"),

    # ── Actualización automática cada 60 segundos ────────────────
    dcc.Interval(id="interval", interval=60 * 1000, n_intervals=0),

    # ── Pie de página ────────────────────────────────────────────
    html.P(
        "Datos con retraso de 15 min. Fuente: Yahoo Finance vía yfinance.",
        className="text-center text-secondary mt-4",
        style={"font-size": "11px"}
    ),
], fluid=True, style={"background-color": "#0d0d1a", "min-height": "100vh", "padding": "20px"})


@app.callback(
    Output("dashboard-content", "children"),
    Input("interval", "n_intervals"),
)
def update_dashboard(n):
    try:
        data = get_market_data()
        return dbc.Row(
            [dbc.Col(make_index_card(name, values), xs=12, sm=6, lg=3, className="mb-4")
             for name, values in data.items()],
            className="g-3"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.P(f"Error al cargar datos: {str(e)}", style={"color": "red"})


if __name__ == "__main__":
    app.run(debug=False)
