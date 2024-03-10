import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash import dcc, html

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