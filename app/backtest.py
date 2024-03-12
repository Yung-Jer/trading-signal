import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def backtest_MACD(ticker, df, param_a, param_b, param_c, num_shares=100, initial_capital=10000):
    close = df['Close']

    exp1 = close.ewm(span=param_a, adjust=False).mean()
    exp2 = close.ewm(span=param_b, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=param_c, adjust=False).mean()
    df['Buy_Signal'] = np.where(df['MACD'] > df['Signal_Line'], 1.0, 0.0)
    df['Positions'] = df['Buy_Signal'].diff()

    # Create a DataFrame `positions`
    positions = pd.DataFrame(index=df.index).fillna(0.0)

    # Buy 100 shares
    positions[ticker] = num_shares * df['Buy_Signal']

    # Store the difference in shares owned compared to previous day
    pos_diff = positions.diff()
    
    # Portfolio value = close price * positions
    portfolio = positions.multiply(df['Close'], axis=0)

    # Add `holdings` to portfolio
    portfolio['holdings'] = (positions.multiply(df['Close'], axis=0)).sum(axis=1)

    # Add `cash` to portfolio
    portfolio['cash'] = initial_capital - (pos_diff.multiply(df['Close'], axis=0)).sum(axis=1).cumsum()   

    # Add `total` to portfolio
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']

    # Add `returns` to portfolio
    portfolio['returns'] = portfolio['total'].pct_change()

    # Plot portfolio value
    # Create subplots
    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.02)
    # Close price
    # fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close", opacity=0.7), row=1, col=1)
    # MACD 
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", opacity=0.8, name="MACD"), row=2, col=1)
    # Signal line for MACD
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal_Line"], mode="lines", opacity=0.8, name="Signal Line"), row=2, col=1)
    # Add up triangles for buy signals and sell signals at the identified points
    fig.add_trace(go.Scatter(
        x=portfolio.loc[df['Positions'] == 1.0].index,
        y=portfolio.total[df['Positions'] == 1.0],
        mode='markers',
        marker=dict(symbol='triangle-up', color='green', size=10),
        name='Buy Signal'), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=portfolio.loc[df['Positions'] == -1.0].index,
        y=portfolio.total[df['Positions'] == -1.0],
        mode='markers',
        marker=dict(symbol='triangle-down', color='red', size=10),
        name='Sell Signal'), row=1, col=1)

    # Update y-axes label
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified")
    fig.update_traces(xaxis='x1')
    
    return portfolio, fig