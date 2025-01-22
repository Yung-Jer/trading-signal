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