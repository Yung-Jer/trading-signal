import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash import dcc, html

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

def generate_backtest_accordion():
    return html.Div(
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        dbc.Row(
                            [
                                dbc.Col([
                                    dbc.Label("Fast line period"),
                                    dbc.Input(placeholder="e.g. 12", type="number", id={"type": "backtest-macd-param", "index": 1}),
                                ]),
                                dbc.Col([
                                    dbc.Label("Slow line period"),
                                    dbc.Input(placeholder="e.g. 26", type="number", id={"type": "backtest-macd-param", "index": 2}),
                                ]),
                                dbc.Col([
                                    dbc.Label("Signal line period"),
                                    dbc.Input(placeholder="e.g. 9", type="number", id={"type": "backtest-macd-param", "index": 3}),
                                ])
                            ],
                            className="ms-2 me-2"
                        ),
                        dbc.Button("Run backtest", id="backtest-macd-button", className="ms-4 mt-3"),
                    ],
                    title="Backtest MACD",
                ),
            ],
            start_collapsed=True,
        )
    )

def generate_MACD_plot(df, a=12, b=26, c=9):
    close = df['Close']

    exp1 = close.ewm(span=a, adjust=False).mean()
    exp2 = close.ewm(span=b, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=c, adjust=False).mean()
    df['Buy_Signal'] = df['MACD'] > df['Signal_Line']
    # Convert boolean values to True/False
    df['Buy_Signal'] = df['Buy_Signal'].astype(bool)
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
    close = df['Close']

    df['Short_MA'] = close.rolling(window=short_window, min_periods=1, center=False).mean()
    df['Long_MA'] = close.rolling(window=long_window, min_periods=1, center=False).mean()
    df['Buy_Signal'] = df['Short_MA'] > df['Long_MA']
    # Convert boolean values to True/False
    df['Buy_Signal'] = df['Buy_Signal'].astype(bool)
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
    length = len(df)
    array_dates = df.index.tolist()
    array_high = df['High'].tolist()
    array_low = df['Low'].tolist()
    array_close = df['Close'].tolist()

    psar = df['Close'].copy()
    psarbull = [None] * len(df)
    psarbear = [None] * len(df)
    
    bull = True
    af = initial_af # initialise acceleration factor

    if length > 0:
        ep = array_low[0] # extreme price
        hp = array_high[0] # extreme high
        lp = array_low[0] # extreme low

    for i in range(2, len(df)):
        if bull:
            # Rising SAR
            psar[i] = psar[i-1] + af * (hp - psar[i-1])
        else:
            # Falling SAR
            psar[i] = psar[i-1] + af * (lp - psar[i-1])

        reverse = False

        # Check reversion point
        if bull:
            if array_low[i] < psar[i]:
                bull = False
                reverse = True
                psar[i] = hp
                lp = array_low[i]
                af = initial_af
        else:
            if array_high[i] > psar[i]:
                bull = True
                reverse = True
                psar[i] = lp
                hp = array_high[i]
                af = initial_af

        if not reverse:
            if bull:
                # Extreme high makes a new high
                if array_high[i] > hp:
                    hp = array_high[i]
                    af = min(af + initial_af, max_af)

                # Check if SAR goes abov prior two periods' lows. 
                # If so, use the lowest of the two for SAR.
                if array_low[i-1] < psar[i]:
                    psar[i] = array_low[i-1]
                if array_low[i-2] < psar[i]:
                    psar[i] = array_low[i-2]

            else:
                # Extreme low makes a new low
                if array_low[i] < lp:
                    lp = array_low[i]
                    af = min(af + initial_af, max_af)

                # Check if SAR goes below prior two periods' highs. 
                # If so, use the highest of the two for SAR.
                if array_high[i-1] > psar[i]:
                    psar[i] = array_high[i-1]
                if array_high[i-2] > psar[i]:
                    psar[i] = array_high[i-2]

        # Save rising SAR
        if bull:
            psarbull[i] = psar[i]
        # Save falling SAR
        else:
            psarbear[i] = psar[i]

    df['psar'] = psar
    df['psarbull'] = psarbull
    df['psarbear'] = psarbear

    df['Buy_Signal'] = True
    # Generate buy signal
    df.loc[df['psarbull'].notnull(), 'Buy_Signal'] = True
    # Generate sell signal
    df.loc[df['psarbear'].notnull(), 'Buy_Signal'] = False
    # Convert boolean values to True/False
    df['Buy_Signal'] = df['Buy_Signal'].astype(bool)
    
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
            html.H3("Moving Average Convergence Divergence (MACD)", className="ms-3"),
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