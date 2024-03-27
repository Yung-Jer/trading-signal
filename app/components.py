import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash import dcc, html
from backtest import gen_MA_signal, gen_MACD_signal, gen_PSAR_signal

input_config = {
    "MACD": [
        {
            "label": "(MACD) Fast line period",
            "placeholder": "e.g. 12",
        },
                    {
            "label": "(MACD) Slow line period",
            "placeholder": "e.g. 26",
        },
        {
            "label": "(MACD) Signal line period",
            "placeholder": "e.g. 9",
        }
    ],
    "MA": [
        {
            "label": "(MA) Short term period",
            "placeholder": "e.g. 40",
        },
                    {
            "label": "(MA) Long term period",
            "placeholder": "e.g. 100",
        },
    ],
    "PSAR": [
        {
            "label": "(PSAR) Initial acceleration factor",
            "placeholder": "e.g. 0.02",
        },
                    {
            "label": "(PSAR) Max acceleration factor",
            "placeholder": "e.g. 0.2",
        },
    ]
}

def generate_list_group_items(name_list): 
    list_group_items = []
    for i in range(len(name_list)):
        if i == 0:
            list_group_items.append(
                dbc.ListGroupItem(
                    name_list[0], 
                    id={
                        "type": "lg",
                        "index": 1
                    },
                    style={
                        "cursor": "pointer",
                        "textDecoration": "none",
                    },
                    action=True,
                    active=True,
                ),
            )
        else:
            list_group_items.append(
                dbc.ListGroupItem(
                    name_list[i],
                    id={
                        "type": "lg",
                        "index": i+1
                    },
                    style={
                        "cursor": "pointer",
                        "textDecoration": "none",
                    },
                    action=True
                ),
            )
    return list_group_items

def generate_line_chart_and_candlestick(df):
    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.02)
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close"), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker=dict(color='rgba(255, 0, 0, 0.9)'), name="Volume"), row=2, col=1)
    # spike line hover extended to all subplots
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

def generate_strategy_and_input(strategy_list):
    return [
        dbc.Col([
            dbc.Label("Strategy"),
            dcc.Dropdown(
                options=["MACD", "MA", "PSAR"],
                value=strategy_list,
                multi=True,
                id="strategy-dropdown"
            )],
            width=2,
        ), 
        dbc.Col(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label(input_config[strat][i]["label"]),
                                dbc.Input(placeholder=input_config[strat][i]["placeholder"], type="number", id={"type": f"backtest-{strat}-param", "index": i+1})
                            ],
                            width=4
                        ) for i in range(len(input_config[strat]))
                    ], 
                    className="mb-2"
                ) for strat in strategy_list
            ],
            id="strategy-param",
            width=10
        )
    ]
    

def generate_backtest_accordion(strategy_list):
    strategy_and_input = generate_strategy_and_input(strategy_list)
    return html.Div(
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        dbc.Row(
                            strategy_and_input,
                            id="strategy-and-input",
                            className="ms-2 me-2 mt-2"
                        ),
                        dbc.Row(dbc.Col(dbc.Button("Run backtest", id="backtest-strategy-button"), width={"width": 2, "offset": 10}, className="mt-4 mb-4")),
                    ],
                    title="Backtest Strategy",
                ),
            ],
            # Always open the accordion item
            active_item="item-0"
        )
    )

def generate_MACD_plot(df, a=12, b=26, c=9):
    df_copy = df.copy()

    df = gen_MACD_signal(df_copy, a, b, c)
    # Identify the points where there is a change from a sell signal to a buy signal and vice versa
    buy_points = df[(df['Buy_Signal'] == True) & (df['Buy_Signal'].shift(1) == False)]
    sell_points = df[(df['Buy_Signal'] == False) & (df['Buy_Signal'].shift(1) == True)]

    # Create subplots
    fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4], shared_xaxes=True, vertical_spacing=0.02)
    # Close price
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", opacity=0.7), row=1, col=1)
    # MACD 
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", opacity=0.8, name="MACD"), row=2, col=1)
    # Signal line for MACD
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal_Line"], mode="lines", opacity=0.8, name="Signal Line"), row=2, col=1)
    # Add up triangles for buy signals and sell signals at the identified points
    fig.add_trace(go.Scatter(
        x=buy_points.index,
        y=buy_points['Close'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=sell_points.index,
        y=sell_points['Close'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'), row=1, col=1)

    # Update y-axes label
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified")
    fig.update_traces(xaxis='x1')

    return dbc.Card(
        [
            html.H3("Moving Average Convergence Divergence (MACD)", className="ms-3"),
            dbc.Row(
                [
                    dbc.Col([
                        dbc.Label("Fast line period"),
                        dbc.Input(placeholder="e.g. 12", type="number", value=a, id={"type": "macd-param", "index": 1}),
                    ]),
                    dbc.Col([
                        dbc.Label("Slow line period"),
                        dbc.Input(placeholder="e.g. 26", type="number", value=b, id={"type": "macd-param", "index": 2}),
                    ]),
                    dbc.Col([
                        dbc.Label("Signal line period"),
                        dbc.Input(placeholder="e.g. 9", type="number", value=c, id={"type": "macd-param", "index": 3}),
                    ])
                ],
                className="ms-2 me-2"
            ),
            dbc.Spinner(dcc.Graph(figure=fig, className="mt-3 mb-3")),
            dbc.Card(
                [
                    dbc.Container(
                        [
                            html.I(className="bi bi-info-circle"),
                            html.B("Tips!", className="ms-2"),
                        ],
                        className="d-flex align-items-center mb-2",
                    ), 
                    dcc.Markdown(
                        """
                         - **Buy signal**: MACD rises above the signal line  
                         - **Sell signal**: MACD falls below the signal line  
                        """,
                        className="me-3"
                    )
                ],
                color="#D7EAF8",
                className="pt-3 pb-3 ps-3 pe-3 d-inline-block"
            ),
        ],
        body=True,
        className="mt-3",
    )

def generate_MA_plot(df, short_window=40, long_window=100):
    df_copy = df.copy()

    df = gen_MA_signal(df_copy, short_window, long_window)

    # Identify the points where there is a change from a sell signal to a buy signal and vice versa
    buy_points = df[(df['Buy_Signal'] == True) & (df['Buy_Signal'].shift(1) == False)]
    sell_points = df[(df['Buy_Signal'] == False) & (df['Buy_Signal'].shift(1) == True)]

    # Create subplots
    fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4], shared_xaxes=True, vertical_spacing=0.02)
    # Close price
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", opacity=0.7), row=1, col=1)
    # Short-term MA
    fig.add_trace(go.Scatter(x=df.index, y=df["Short_MA"], mode="lines", opacity=0.8, name="Short-term MA"), row=2, col=1)
    # Long-term MA
    fig.add_trace(go.Scatter(x=df.index, y=df["Long_MA"], mode="lines", opacity=0.8, name="Long-term MA"), row=2, col=1)
    # Add up triangles for buy signals and sell signals at the identified points
    fig.add_trace(go.Scatter(
        x=buy_points.index,
        y=buy_points['Close'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=sell_points.index,
        y=sell_points['Close'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'), row=1, col=1)

    # Update y-axes label
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)
    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified")
    fig.update_traces(xaxis='x1')

    return dbc.Card(
        [
            html.H3("Moving Averages (MA)", className="ms-3"),
            dbc.Row(
                [
                    dbc.Col([
                        dbc.Label("Short-term period"),
                        dbc.Input(placeholder="e.g. 40", type="number", value=short_window, id={"type": "ma-param", "index": 1}),
                    ]),
                    dbc.Col([
                        dbc.Label("Long-term period"),
                        dbc.Input(placeholder="e.g. 100", type="number", value=long_window, id={"type": "ma-param", "index": 2}),
                    ]),
                ],
                className="ms-2 me-2"
            ),
            dbc.Spinner(dcc.Graph(figure=fig, className="mt-3 mb-3")),
            dbc.Card(
                [
                    dbc.Container(
                        [
                            html.I(className="bi bi-info-circle"),
                            html.B("Tips!", className="ms-2"),
                        ],
                        className="d-flex align-items-center mb-2",
                    ), 
                    dcc.Markdown(
                        """
                         - **Buy signal**: short-term MA crosses above the long-term MA (golden cross)  
                         - **Sell signal**: short-term MA crosses below the long-term MA (dead/death cross) 
                        """,
                        className="me-3"
                    )
                ],
                color="#D7EAF8",
                className="pt-3 pb-3 ps-3 pe-3 d-inline-block"
            ),
        ],
        body=True,
        className="mt-3",
    )

def generate_PSAR_plot(df, initial_af=0.02, max_af=0.2):
    df_copy = df.copy()

    df = gen_PSAR_signal(df_copy, initial_af, max_af)
    
    # Identify the points where there is a change from a sell signal to a buy signal and vice versa
    buy_points = df[(df['Buy_Signal'] == True) & (df['Buy_Signal'].shift(1) == False)]
    sell_points = df[(df['Buy_Signal'] == False) & (df['Buy_Signal'].shift(1) == True)]

    # Create subplots
    fig = make_subplots(rows=2, cols=1, row_heights=[0.6, 0.4], shared_xaxes=True, vertical_spacing=0.02)
    # Close price
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", opacity=0.7), row=1, col=1)
    # psar
    fig.add_trace(go.Scatter(x=df.index, y=df["psar"], mode="lines", opacity=0.8, name="PSAR"), row=2, col=1)
    # psanbull
    fig.add_trace(go.Scatter(x=df.index, y=df["psarbull"], mode="lines", opacity=0.8, name="PSAR Bull Line"), row=2, col=1)
    # psarbear
    fig.add_trace(go.Scatter(x=df.index, y=df["psarbear"], mode="lines", opacity=0.8, name="PSAR Bear Line"), row=2, col=1)
    # Add up triangles for buy signals and sell signals at the identified points
    fig.add_trace(go.Scatter(
        x=buy_points.index,
        y=buy_points['Close'],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=sell_points.index,
        y=sell_points['Close'],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'), row=1, col=1)

    # Update y-axes label
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="PSAR", row=2, col=1)
    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified")
    fig.update_traces(xaxis='x1')

    return dbc.Card(
        [
            html.H3("Parabolic Stop and Reverse (PSAR)", className="ms-3"),
            dbc.Row(
                [
                    dbc.Col([
                        dbc.Label("Initial acceleration factor"),
                        dbc.Input(placeholder="e.g. 0.02", type="number", value=initial_af, id={"type": "psar-param", "index": 1}),
                    ]),
                    dbc.Col([
                        dbc.Label("Max acceleration factor"),
                        dbc.Input(placeholder="e.g. 0.2", type="number", value=max_af, id={"type": "psar-param", "index": 2}),
                    ]),
                ],
                className="ms-2 me-2"
            ),
            dbc.Spinner(dcc.Graph(figure=fig, className="mt-3 mb-3")),
            dbc.Card(
                [
                    dbc.Container(
                        [
                            html.I(className="bi bi-info-circle"),
                            html.B("Tips!", className="ms-2"),
                        ],
                        className="d-flex align-items-center mb-2",
                    ), 
                    dcc.Markdown(
                        """
                         - **Buy signal**: if falling SAR goes below the price  
                         - **Sell signal**: if rising SAR goes above the price  
                        """,
                        className="me-3"
                    )
                ],
                color="#D7EAF8",
                className="pt-3 pb-3 ps-3 pe-3 d-inline-block"
            ),
        ],
        body=True,
        className="mt-3",
    )

def blank_figure():
    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None)
    
    return fig