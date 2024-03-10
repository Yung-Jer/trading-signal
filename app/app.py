import json
import os
import re
import sys
import time
import requests_cache
import pandas as pd
from io import StringIO
import datetime

import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from dash import Dash, Input, Output, State, dcc, html, callback, ALL, MATCH, callback_context

from data import get_single_stock
from components import generate_list_group_items, generate_MACD_plot, generate_MA_plot
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------
# Init app
# --------


session = requests_cache.CachedSession(cache_name='cache', backend='sqlite')

# just add headers to your session and provide it to the reader
session.headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
                   'Accept': 'application/json;charset=utf-8'}

TRADING_LOGO = "./assets/trading-logo-design.jpg"

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
load_figure_template("flatly")

external_stylesheets = [dbc.themes.FLATLY, dbc_css, dbc.icons.BOOTSTRAP]

app = Dash(
    __name__,
    title="Trading Signal",
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True
)

df = get_single_stock("AAPL", period="1y")
df.rename(columns={"Adj Close": "Adj_Close"}, inplace=True)
# df['Moving_Average_26'] = df['Adj_Close'].rolling(window=26, min_periods=0).mean()
df.dropna(inplace=True)

fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.02)
fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close"), row=1, col=1)
# fig.add_trace(go.Scatter(x=df.index, y=df["Moving_Average_26"], mode="lines", name="Moving Average (26 days)"), row=1, col=1)
fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker=dict(color='rgba(255, 0, 0, 0.9)'), name="Volume"), row=2, col=1)
    #  spike line hover extended to all subplots
fig.update_layout(hovermode="x unified")
# Update y-axis titles for the subplots
fig.update_yaxes(title_text="Price ($)", row=1, col=1)
fig.update_yaxes(title_text="Volume (unit)", row=2, col=1)
fig.update_traces(xaxis='x1')

fig2 = go.Figure(
    data=[
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )
    ]
)
fig2.update_layout(yaxis=dict(title="Price ($)"))

# --------
# Components
# --------

search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(type="search", placeholder="e.g. AAPL, TSLA, ...")),
        dbc.Col(
            dbc.Button(
                "Search", color="primary", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(dbc.NavbarBrand("Trading Signal", className="ms-2 h1")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                search_bar,
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
    ),
    color="#2c3e50",
    dark=True,
)

list_group_tabs = dbc.ListGroup(
    generate_list_group_items(["Chart Analysis", "MACD", "MA"]),
    id="lg",
    flush=True,
    className="mt-4",
    style={"borderRadius": "7px"}
),

tab_1_content = dbc.Card(
    [
        html.H3("Line Chart", className="ms-3"),
        dbc.Spinner(dcc.Graph(figure=fig, className="mt-3 mb-3")),
        html.H3("Candlestick Chart", className="ms-3"),
        dbc.Spinner(dcc.Graph(figure=fig2, className="mt-3 mb-3")),
    ],
    body=True,
    className="mt-3",
)

content = dbc.Row(
    dbc.Col(
        [
            dbc.Row(
                dbc.DropdownMenu(
                    label="Ticker",
                    menu_variant="dark",
                    children=[
                        dbc.DropdownMenuItem("AAPL", id={"type": "dropdown", "index": 1}),
                        dbc.DropdownMenuItem("TSLA", id={"type": "dropdown", "index": 2}),
                        dbc.DropdownMenuItem("VOOV", id={"type": "dropdown", "index": 3}),
                        dbc.DropdownMenuItem("IVV", id={"type": "dropdown", "index": 4}),
                        dbc.DropdownMenuItem("VTI", id={"type": "dropdown", "index": 5}),
                    ],
                ),
                className="mt-3"
            ),
            html.Br(),
            html.H3(children='AAPL', id="title"),
            html.P(children=f"Data as of {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.", id="dt-title"),
            dbc.Row(
                [
                    dbc.Col(
                        list_group_tabs,
                        width=3,
                    ),
                    dbc.Col(
                        tab_1_content,
                        id="chart",
                        width=9
                    )
                ],
                key="main-figure"
            ),
        ], 
    ),
    className="mb-5 ps-4 pe-4"
)

# ----------
# App layout
# ----------

def serve_layout():
    return html.Div(
        [
            navbar,
            dcc.Store(
                id="df-store",
                data=df.to_json(date_format="iso", orient="split"),
                storage_type="memory",
            ),
            dbc.Container(
                content,
                fluid=True,
                className="ps-5 pe-5"
            )
        ]
    )

app.layout = serve_layout

@app.callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_navbar_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output({"type": "lg", "index": ALL}, "active", allow_duplicate=True),
    Input({"type": "lg", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def change_active(n_clicks):
    ctx = callback_context
    input_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
    idx = int(input_id["index"])
    
    bool_array = [False] * len(n_clicks)
    bool_array[idx-1] = True

    return bool_array

@app.callback(
    Output("df-store", "data"),
    Output("title", "children"),
    Output("dt-title", "children"),
    Output("chart", "children", allow_duplicate=True),
    Output({"type": "lg", "index": ALL}, "active", allow_duplicate=True),
    Input({"type": "dropdown", "index": ALL}, "n_clicks"),
    State({"type": "dropdown", "index": ALL}, "children"),
    State({"type": "lg", "index": ALL}, "active"),
    prevent_initial_call=True
)
def set_ticker_df(n_clicks, ticker_names, active_list):
    ctx = callback_context
    
    triggered_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
    idx = int(triggered_id["index"])

    ticker_name = ticker_names[idx - 1]  # Adjust index to match dropdowns
    df = get_single_stock(ticker_name, period="5y")
    df.rename(columns={"Adj Close": "Adj_Close"}, inplace=True)
    df.dropna(inplace=True)
    return [
        df.to_json(date_format="iso", orient="split"), 
        ticker_name, 
        f"Data as of {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
        html.Div(),
        [False] * len(active_list)
    ]

@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": 1}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True
)
def generate_tab_1_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(json_df, orient='split')
    df_copy = df.copy()
    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.02)
    fig.add_trace(go.Scatter(x=df_copy.index, y=df_copy["Close"], mode="lines", name="Close"), row=1, col=1)
    # fig.add_trace(go.Scatter(x=df.index, y=df["Moving_Average_26"], mode="lines", name="Moving Average (26 days)"), row=1, col=1)
    fig.add_trace(go.Bar(x=df_copy.index, y=df_copy["Volume"], marker=dict(color='rgba(255, 0, 0, 0.9)'), name="Volume"), row=2, col=1)
    
    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified")
    # Update y-axis titles for the subplots
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume (unit)", row=2, col=1)
    fig.update_traces(xaxis='x1')

    fig2 = go.Figure(
        data=[
            go.Candlestick(
                x=df_copy.index,
                open=df_copy['Open'],
                high=df_copy['High'],
                low=df_copy['Low'],
                close=df_copy['Close']
            )
        ]
    )
    fig2.update_layout(yaxis=dict(title="Price ($)"))
    return dbc.Card(
        [
            html.H3("Line Chart", className="ms-3"),
            dbc.Spinner(dcc.Graph(figure=fig, className="mt-3 mb-3")),
            html.H3("Candlestick Chart", className="ms-3"),
            dbc.Spinner(dcc.Graph(figure=fig2, className="mt-3 mb-3")),
        ],
        body=True,
        className="mt-3",
    )

@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": 2}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True
)
def generate_tab_2_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(json_df, orient='split')
    df_copy = df.copy()
    # Get adjusted close column
    return generate_MACD_plot(df_copy)
    
@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "macd-param", "index": ALL}, "value"),
    State("df-store", "data"),
    State("chart", "children"),
    prevent_initial_call=True
)
def change_MACD_param(MACD_param, json_df, prev_figure):
    # Catch exception when users are typing the input for the MACD settings
    # Return previous figure if there is any exception
    try:
        # Read the JSON data into a pandas DataFrame
        df = pd.read_json(json_df, orient='split')
        df_copy = df.copy()
        a, b, c = MACD_param
        
        new_figure = generate_MACD_plot(df_copy, a, b, c)
        return new_figure
    
    except Exception:
        return prev_figure
    
@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": 3}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True
)
def generate_tab_3_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(json_df, orient='split')
    df_copy = df.copy()
    # Get adjusted close column
    return generate_MA_plot(df_copy)

@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "ma-param", "index": ALL}, "value"),
    State("df-store", "data"),
    State("chart", "children"),
    prevent_initial_call=True
)
def change_MA_param(MA_param, json_df, prev_figure):
    # Catch exception when users are typing the input for the MACD settings
    # Return previous figure if there is any exception
    try:
        # Read the JSON data into a pandas DataFrame
        df = pd.read_json(json_df, orient='split')
        df_copy = df.copy()
        short_window, long_window = MA_param
        
        new_figure = generate_MA_plot(df_copy, short_window, long_window)
        return new_figure
    
    except Exception:
        return prev_figure

if __name__ == '__main__':
    app.run(debug=True)
