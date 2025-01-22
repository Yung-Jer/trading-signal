import datetime
import json
from io import StringIO

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from backtest import (
    gen_CCI_signal,
    gen_MA_signal,
    gen_MACD_signal,
    gen_PSAR_signal,
)
from components import (
    blank_figure,
    generate_backtest_accordion,
    generate_CCI_plot,
    generate_line_chart_and_candlestick,
    generate_list_group_items,
    generate_MA_plot,
    generate_MACD_plot,
    generate_PSAR_plot,
    generate_strategy_and_input,
)
from dash import (
    ALL,
    MATCH,
    Dash,
    Input,
    Output,
    State,
    callback,
    callback_context,
    dcc,
    html,
    no_update,
)
from dash_bootstrap_templates import load_figure_template
from flask_caching import Cache
from plotly.subplots import make_subplots

# --------
# Init app
# --------

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
load_figure_template("flatly")

external_stylesheets = [dbc.themes.FLATLY, dbc_css, dbc.icons.BOOTSTRAP]

app = Dash(
    __name__,
    title="Trading Signal",
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)


cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": ".cache-directory",
        # Threshold based on number of CSV files to cache
        "CACHE_THRESHOLD": 10,
    },
)
cache.clear()


def download_stock(ticker, start_date, end_date=None):
    if end_date is None:
        end_date = datetime.date.today()
    if isinstance(start_date, datetime.date):
        start_date = start_date.strftime("%Y-%m-%d")
    if isinstance(end_date, datetime.date):
        end_date = end_date.strftime("%Y-%m-%d")

    # Cache timeout set to 1 day
    @cache.memoize(timeout=60 * 15)
    def download_stock_helper(ticker, start_date, end_date):
        df = yf.download(ticker, start_date, end_date)
        df.columns = df.columns.get_level_values(0)
        return df

    return download_stock_helper(ticker, start_date, end_date)


today = datetime.date.today()
one_year_ago = today - datetime.timedelta(days=365)
half_year_ago = today - datetime.timedelta(days=180)


df = download_stock("VOO", one_year_ago, half_year_ago)
df.rename(columns={"Adj Close": "Adj_Close"}, inplace=True)
df.dropna(inplace=True)

# --------
# Components
# --------

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
        ],
    ),
    color="#2c3e50",
    dark=True,
)

INDICATOR_LIST = ["Chart Analysis", "Moving Average (MA)", "MACD", "Parabolic SAR", "CCI"]

list_group_tabs = (
    dbc.ListGroup(
        generate_list_group_items(
            INDICATOR_LIST
        ),
        id="lg",
        flush=True,
        className="mt-4",
        style={"borderRadius": "7px"},
    ),
)

line_candlestick_chart = generate_line_chart_and_candlestick(df)

content = dbc.Row(
    dbc.Col(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(html.B("Symbol: ")),
                            dbc.Input(id="ticker-input", debounce=True),
                        ]
                    ),
                    dbc.Col(
                        [
                            dbc.Label(html.B("Date Range: ")),
                            html.Br(),
                            dcc.DatePickerRange(
                                id="date-picker-range",
                                start_date=one_year_ago,
                                end_date=today,
                                display_format="YYYY-MM-DD",
                                clearable=True,
                                with_portal=True,
                            ),
                        ],
                        className="ms-3",
                    ),
                ],
                className="mt-3",
            ),
            html.Br(),
            html.Div(
                [
                    html.H3(
                        children="VOO",
                        className="d-inline-block align-items-center",
                        id="ticker-title",
                    ),
                    html.H6(
                        children="(180 days)",
                        className="d-inline-block align-items-center mt-3 ms-2",
                        id="time-horizon",
                    ),
                ]
            ),
            html.P(
                children=f"Data as of {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
                id="dt-title",
            ),
            dbc.Alert("No such ticker found!", id="ticker-warning", color="warning", is_open=False),
            dbc.Tabs(
                [
                    dbc.Tab(
                        dbc.Card(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        list_group_tabs,
                                        width=3,
                                    ),
                                    dbc.Col(
                                        line_candlestick_chart, id="chart", width=9
                                    ),
                                ],
                                key="main-figure",
                            ),
                            body=True,
                        ),
                        label="Visualization",
                    ),
                ]
            ),
        ],
    ),
    className="mb-5 ps-4 pe-4",
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
            dcc.Store(
                id="ticker-store", data="VOO", storage_type="memory"
            ),
            dbc.Container(content, fluid=True, className="ps-5 pe-5"),
        ]
    )


app.layout = serve_layout


@app.callback(
    Output({"type": "lg", "index": ALL}, "active", allow_duplicate=True),
    Input({"type": "lg", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def change_active(n_clicks):
    ctx = callback_context
    input_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
    idx = int(input_id["index"])

    bool_array = [False] * len(n_clicks)
    bool_array[idx - 1] = True

    return bool_array


@app.callback(
    Output("df-store", "data"),
    Output("ticker-title", "children"),
    Output("time-horizon", "children"),
    Output("dt-title", "children"),
    Output("chart", "children", allow_duplicate=True),
    Output({"type": "lg", "index": ALL}, "active", allow_duplicate=True),
    Output("ticker-store", "data"),
    Output("ticker-warning", "is_open"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input("ticker-input", "value"),
    State("ticker-store", "data"),
    State({"type": "lg", "index": ALL}, "active"),
    prevent_initial_call=True,
)
def set_ticker_df(
    start_date,
    end_date,
    value,
    curr_ticker,
    active_list,
):
    df = download_stock(value, start_date, end_date)
    if len(df) == 0:
        return [no_update] * 5 + [[True if not i else False for i in range(len(active_list))], curr_ticker, True]
    # update back the ticker and period store
    updated_ticker = value
    curr_period = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.datetime.strptime(start_date, "%Y-%m-%d")).days
    ticker_title, time_horizon = value, f"({curr_period} days)" if curr_period > 1 else f"({curr_period} day)"

    df = df.rename(columns={"Adj Close": "Adj_Close"}).copy()
    df = df.dropna()

    return [
        df.to_json(date_format="iso", orient="split"),
        ticker_title,
        time_horizon,
        f"Data as of {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
        generate_line_chart_and_candlestick(df),
        [True if not i else False for i in range(len(active_list))],
        updated_ticker,
        False
    ]


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": INDICATOR_LIST.index("Chart Analysis")+1}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True,
)
def generate_chart_analysis_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(StringIO(json_df), orient="split")
    df_copy = df.copy()
    fig = make_subplots(
        rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.02
    )
    fig.add_trace(
        go.Scatter(x=df_copy.index, y=df_copy["Close"], mode="lines", name="Close"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_copy.index,
            y=df_copy["Volume"],
            marker=dict(color="rgba(255, 0, 0, 0.9)"),
            name="Volume",
        ),
        row=2,
        col=1,
    )

    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified")
    # Update y-axis titles for the subplots
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume (unit)", row=2, col=1)
    fig.update_traces(xaxis="x1")

    fig2 = go.Figure(
        data=[
            go.Candlestick(
                x=df_copy.index,
                open=df_copy["Open"],
                high=df_copy["High"],
                low=df_copy["Low"],
                close=df_copy["Close"],
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
    Input({"type": "lg", "index": INDICATOR_LIST.index("MACD")+1}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True,
)
def generate_MACD_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(StringIO(json_df), orient="split")
    df_copy = df.copy()
    # Get adjusted close column
    return generate_MACD_plot(df_copy)


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "macd-param", "index": ALL}, "value"),
    State("df-store", "data"),
    State("chart", "children"),
    prevent_initial_call=True,
)
def change_MACD_param(MACD_param, json_df, prev_figure):
    # Catch exception when users are typing the input for the MACD settings
    # Return previous figure if there is any exception
    try:
        # Read the JSON data into a pandas DataFrame
        df = pd.read_json(StringIO(json_df), orient="split")
        df_copy = df.copy()
        a, b, c = MACD_param

        new_figure = generate_MACD_plot(df_copy, a, b, c)
        return new_figure

    except Exception:
        return prev_figure


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": INDICATOR_LIST.index("Moving Average (MA)")+1}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True,
)
def generate_MA_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(StringIO(json_df), orient="split")
    df_copy = df.copy()
    # Get adjusted close column
    return generate_MA_plot(df_copy)


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "ma-param", "index": ALL}, "value"),
    State("df-store", "data"),
    State("chart", "children"),
    prevent_initial_call=True,
)
def change_MA_param(MA_param, json_df, prev_figure):
    # Catch exception when users are typing the input for the MACD settings
    # Return previous figure if there is any exception
    try:
        # Read the JSON data into a pandas DataFrame
        df = pd.read_json(StringIO(json_df), orient="split")
        df_copy = df.copy()
        short_window, long_window = MA_param

        new_figure = generate_MA_plot(df_copy, short_window, long_window)
        return new_figure

    except Exception:
        return prev_figure


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": INDICATOR_LIST.index("Parabolic SAR")+1}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True,
)
def generate_PSAR_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(StringIO(json_df), orient="split")
    df_copy = df.copy()
    # Get adjusted close column
    return generate_PSAR_plot(df_copy)


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "psar-param", "index": ALL}, "value"),
    State("df-store", "data"),
    State("chart", "children"),
    prevent_initial_call=True,
)
def change_PSAR_param(PSAR_param, json_df, prev_figure):
    # Catch exception when users are typing the input for the MACD settings
    # Return previous figure if there is any exception
    try:
        # Read the JSON data into a pandas DataFrame
        df = pd.read_json(StringIO(json_df), orient="split")
        df_copy = df.copy()
        initial_af, max_af = PSAR_param

        new_figure = generate_PSAR_plot(df_copy, initial_af, max_af)
        return new_figure

    except Exception:
        return prev_figure


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "lg", "index": INDICATOR_LIST.index("CCI")+1}, "n_clicks"),
    State("df-store", "data"),
    prevent_initial_call=True,
)
def generate_CCI_content(n_clicks, json_df):
    # Read the JSON data into a pandas DataFrame
    df = pd.read_json(StringIO(json_df), orient="split")
    df_copy = df.copy()
    # Get adjusted close column
    return generate_CCI_plot(df_copy)


@app.callback(
    Output("chart", "children", allow_duplicate=True),
    Input({"type": "cci-param", "index": ALL}, "value"),
    State("df-store", "data"),
    State("chart", "children"),
    prevent_initial_call=True,
)
def change_CCI_param(CCI_param, json_df, prev_figure):
    # Catch exception when users are typing the input for the MACD settings
    # Return previous figure if there is any exception
    try:
        # Read the JSON data into a pandas DataFrame
        df = pd.read_json(StringIO(json_df), orient="split")
        df_copy = df.copy()
        window_size, constant = CCI_param

        new_figure = generate_CCI_plot(df_copy, window_size, constant)
        return new_figure

    except Exception:
        return prev_figure


# @app.callback(
#     Output("backtest-output", "children", allow_duplicate=True),
#     Input("backtest-strategy-button", "n_clicks"),
#     State("strategy-dropdown", "value"),
#     State("strategy-param", "children"),
#     State("df-store", "data"),
#     prevent_initial_call=True,
# )
# def generate_backtest_chart(n_clicks, strategy_list, strategy_param_component, json_df):
#     # Read the JSON data into a pandas DataFrame
#     df = pd.read_json(StringIO(json_df), orient="split").copy()
#     df["Return"] = df["Close"] / df["Close"].shift(1)
#     df["Buy_Signal"] = np.where(df["Return"] > 1, 1, 0)
#     df.dropna(inplace=True)
#     strategy_param = {strat: [] for strat in strategy_list}

#     try:
#         for ele in strategy_param_component:
#             for idx in range(len(ele["props"]["children"])):
#                 strat = ele["props"]["children"][idx]["props"]["children"][1]["props"][
#                     "id"
#                 ]["type"].split("-")[1]
#                 val = ele["props"]["children"][idx]["props"]["children"][1]["props"][
#                     "value"
#                 ]
#                 strategy_param[strat].append(val)
#     except KeyError:
#         print(strategy_param)
#         return dbc.Alert(
#             "Please specify all the strategy parameters.",
#             is_open=True,
#             duration=5000,
#             className="mt-3 mb-3 ms-3 me-3",
#         )
#     else:
#         print(strategy_param)
#         buy_signal_series = []
#         for strat in strategy_param:
#             if strat == "MACD":
#                 df_copy = df.copy()
#                 buy_signal_series.append(
#                     gen_MACD_signal(df_copy, *strategy_param[strat])[
#                         "Buy_Signal"
#                     ].tolist()
#                 )
#             if strat == "MA":
#                 df_copy = df.copy()
#                 buy_signal_series.append(
#                     gen_MA_signal(df_copy, *strategy_param[strat])[
#                         "Buy_Signal"
#                     ].tolist()
#                 )
#             if strat == "PSAR":
#                 df_copy = df.copy()
#                 buy_signal_series.append(
#                     gen_PSAR_signal(df_copy, *strategy_param[strat])[
#                         "Buy_Signal"
#                     ].tolist()
#                 )

#         X = np.column_stack(buy_signal_series)
#         num_column = X.shape[1]
#         # Perform majority voting along the left columns
#         majority_vote = np.sum(X, axis=1)

#         # Define a threshold for majority voting
#         threshold = (
#             2 / 3 * num_column
#         )  # Adjust as needed, for example, if 2 out of 3 are True, it's considered a majority
#         print(f"Threshold: {threshold}")

#         # Create the new column based on the majority voting result
#         new_column = (majority_vote >= threshold).astype(int)

#         df["Buy_Signal_Predict"] = new_column

#         portfolio, fig = backtest(df)
#         # print(portfolio.tail(20))
#         return dbc.Spinner(dcc.Graph(figure=fig, className="mt-3 mb-3"))


# @app.callback(
#     Output("strategy-and-input", "children"),
#     Input("strategy-dropdown", "value"),
#     prevent_initial_call=True,
# )
# def test_strategy(strategy_values):
#     strategy_and_input = generate_strategy_and_input(strategy_values)

#     return strategy_and_input


if __name__ == "__main__":
    app.run()
