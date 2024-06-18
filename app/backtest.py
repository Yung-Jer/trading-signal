import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def gen_MACD_signal(df, a, b, c):
    df = df.copy()
    close = df["Close"]

    exp1 = close.ewm(span=a, adjust=False).mean()
    exp2 = close.ewm(span=b, adjust=False).mean()
    df["MACD"] = exp1 - exp2
    df["Signal_Line"] = df["MACD"].ewm(span=c, adjust=False).mean()
    df["Buy_Signal"] = df["MACD"] > df["Signal_Line"]
    # Convert boolean values to True/False
    df["Buy_Signal"] = df["Buy_Signal"].astype(bool)

    return df


def gen_MA_signal(df, short_window=40, long_window=100):
    df = df.copy()
    close = df["Close"]

    df["Short_MA"] = close.rolling(
        window=short_window, min_periods=1, center=False
    ).mean()
    df["Long_MA"] = close.rolling(
        window=long_window, min_periods=1, center=False
    ).mean()
    df["Buy_Signal"] = df["Short_MA"] > df["Long_MA"]
    # Convert boolean values to True/False
    df["Buy_Signal"] = df["Buy_Signal"].astype(bool)

    return df


def gen_PSAR_signal(df, initial_af=0.02, max_af=0.2):
    df = df.copy()
    length = len(df)

    array_high = df["High"].tolist()
    array_low = df["Low"].tolist()

    psar = df["Close"].copy()
    psarbull = [None] * len(df)
    psarbear = [None] * len(df)

    bull = True
    af = initial_af  # initialise acceleration factor

    if length > 0:
        ep = array_low[0]  # extreme price
        hp = array_high[0]  # extreme high
        lp = array_low[0]  # extreme low

    for i in range(2, len(df)):
        if bull:
            # Rising SAR
            psar[i] = psar[i - 1] + af * (hp - psar[i - 1])
        else:
            # Falling SAR
            psar[i] = psar[i - 1] + af * (lp - psar[i - 1])

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
                if array_low[i - 1] < psar[i]:
                    psar[i] = array_low[i - 1]
                if array_low[i - 2] < psar[i]:
                    psar[i] = array_low[i - 2]

            else:
                # Extreme low makes a new low
                if array_low[i] < lp:
                    lp = array_low[i]
                    af = min(af + initial_af, max_af)

                # Check if SAR goes below prior two periods' highs.
                # If so, use the highest of the two for SAR.
                if array_high[i - 1] > psar[i]:
                    psar[i] = array_high[i - 1]
                if array_high[i - 2] > psar[i]:
                    psar[i] = array_high[i - 2]

        # Save rising SAR
        if bull:
            psarbull[i] = psar[i]
        # Save falling SAR
        else:
            psarbear[i] = psar[i]

    df["psar"] = psar
    df["psarbull"] = psarbull
    df["psarbear"] = psarbear

    df["Buy_Signal"] = True
    # Generate buy signal
    df.loc[df["psarbull"].notnull(), "Buy_Signal"] = True
    # Generate sell signal
    df.loc[df["psarbear"].notnull(), "Buy_Signal"] = False
    # Convert boolean values to True/False
    df["Buy_Signal"] = df["Buy_Signal"].astype(bool)

    return df


def gen_CCI_signal(df, window_size=20, constant=0.015):
    df = df.copy()
    df["Typical Price"] = (df["High"] + df["Low"] + df["Close"]) / 3

    df["SMA"] = (
        df["Typical Price"]
        .rolling(window=window_size, min_periods=1, center=False)
        .mean()
    )

    df["Mean Deviation"] = (
        df["Typical Price"]
        .rolling(window=window_size, min_periods=1, center=False)
        .std()
    )

    df["CCI"] = (df["Typical Price"] - df["SMA"]) / (constant * df["Mean Deviation"])

    # Generate buy signal
    df["Buy_Signal"] = df["CCI"] > 100
    # Convert boolean values to True/False
    df["Buy_Signal"] = df["Buy_Signal"].astype(bool)

    return df


def portfolio_computation(ticker_df, num_shares=10, initial_capital=10000):
    # Create a DataFrame `positions`
    positions = pd.DataFrame(index=ticker_df.index).fillna(0.0)

    # Hold num_shares of stock when the buy signal line is predicted to be crossed over
    positions["holdings"] = num_shares * ticker_df["Buy_Signal_Predict"]

    # Take the difference to know when is the exact day to buy num_shares and hold it
    # subsequently until the following sell signal
    pos_diff = positions.diff()

    # Portfolio value = close price * positions
    portfolio = positions.multiply(ticker_df["Close"], axis=0)

    # Add `cash` to portfolio
    portfolio["cash"] = (
        initial_capital
        - (pos_diff.multiply(ticker_df["Close"], axis=0)).sum(axis=1).cumsum()
    )

    # Add `total` to portfolio
    portfolio["total"] = portfolio["cash"] + portfolio["holdings"]

    # Add `returns` to portfolio
    portfolio["returns"] = portfolio["total"].pct_change()

    return portfolio


def backtest(ticker_df, num_shares=10, initial_capital=10000):

    portfolio = portfolio_computation(ticker_df, num_shares, initial_capital)

    ticker_df["Positions_Predict"] = ticker_df["Buy_Signal_Predict"].diff()
    ticker_df = ticker_df.fillna(0.0)
    portfolio = portfolio.fillna(0.0)

    print(ticker_df.iloc[:20])
    print(portfolio.iloc[:20])
    # Create subplots
    fig = make_subplots(
        rows=3,
        cols=1,
        row_heights=[0.5, 0.2, 0.3],
        shared_xaxes=True,
        vertical_spacing=0.07,
    )

    # Total
    fig.add_trace(
        go.Scatter(
            x=portfolio.index,
            y=portfolio["total"],
            mode="lines",
            opacity=0.9,
            name="Portfolio Total",
        ),
        row=1,
        col=1,
    )

    # Add up triangles for buy signals and sell signals at the identified points
    fig.add_trace(
        go.Scatter(
            x=portfolio.loc[ticker_df["Positions_Predict"] == 1.0].index,
            y=portfolio.total[ticker_df["Positions_Predict"] == 1.0],
            mode="markers",
            marker=dict(symbol="triangle-up", color="green", size=10),
            name="Buy Signal",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=portfolio.loc[ticker_df["Positions_Predict"] == -1.0].index,
            y=portfolio.total[ticker_df["Positions_Predict"] == -1.0],
            mode="markers",
            marker=dict(symbol="triangle-down", color="red", size=10),
            name="Sell Signal",
        ),
        row=1,
        col=1,
    )

    # Holdings vs cash plots
    fig.add_trace(
        go.Scatter(
            x=portfolio.index,
            y=portfolio["holdings"],
            mode="lines",
            opacity=0.8,
            name="Holding Value",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=portfolio.index,
            y=portfolio["cash"],
            mode="lines",
            opacity=0.8,
            name="Cash",
        ),
        row=2,
        col=1,
    )

    # Close
    fig.add_trace(
        go.Scatter(
            x=ticker_df.index,
            y=ticker_df["Close"],
            mode="lines",
            opacity=0.8,
            name="Close",
        ),
        row=3,
        col=1,
    )
    # Add up triangles for buy signals and sell signals at the identified points
    fig.add_trace(
        go.Scatter(
            x=ticker_df.loc[ticker_df["Positions_Predict"] == 1.0].index,
            y=ticker_df.Close[ticker_df["Positions_Predict"] == 1.0],
            mode="markers",
            marker=dict(symbol="triangle-up", color="green", size=10),
            name="Buy Signal",
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=ticker_df.loc[ticker_df["Positions_Predict"] == -1.0].index,
            y=ticker_df.Close[ticker_df["Positions_Predict"] == -1.0],
            mode="markers",
            marker=dict(symbol="triangle-down", color="red", size=10),
            name="Sell Signal",
        ),
        row=3,
        col=1,
    )

    # Update y-axes label
    fig.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Holding vs Cash ($)", row=2, col=1)
    fig.update_yaxes(title_text="Close ($)", row=3, col=1)
    #  spike line hover extended to all subplots
    fig.update_layout(hovermode="x unified", height=650)
    fig.update_traces(xaxis="x1")

    return portfolio, fig
