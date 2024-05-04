import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf

def get_stocks(tickers, period="10y"):
    return yf.download(tickers, period=period)

def get_returns_for_multiple_stocks(tickers: list, start_date: str, end_date: str) -> pd.DataFrame:
    '''
    Function that downloads data directly from Yahoo Finance,
    computes the Log Returns series for each ticker, and returns a DataFrame 
    containing the Log Returns of all specified tickers.
    
    Parameters:
    - tickers (list): List of Stock Tickers.
    - start_date, end_date (str): Start and end dates in the format 'YYYY-MM-DD'.
    
    Returns:
    - returns_df (pd.DataFrame): A DataFrame with dates as indexes, and columns corresponding
                                 to the log returns series of each ticker.
    '''

    # initialise output dataframe
    returns_df = pd.DataFrame()
    
    for ticker in tickers:
        # retrieve stock data (includes Date, OHLC, Volume, Adjusted Close)
        format='%Y-%m-%d'
        s = yf.download(ticker, dt.datetime.strptime(start_date, format), dt.datetime.strptime(end_date, format))
        # calculate log returns
        s['Log Returns'] = np.log(s['Adj Close']/s['Adj Close'].shift(1))
        # append to returns_df
        returns_df[ticker] = s['Log Returns']
        
    # skip the first row (that will be NA)
    # and fill other NA values by 0 in case there are trading halts on specific days
    # returns_df = returns_df.iloc[1:].fillna(0)
    returns_df = returns_df.dropna()
    
    return returns_df

def get_close_for_multiple_stocks(tickers, start_date, end_date):
    '''
    Function that downloads data directly from Yahoo Finance,
    computes the Log Returns series for each ticker, and returns a DataFrame 
    containing the Log Returns of all specified tickers.
    
    Parameters:
    - tickers (list): List of Stock Tickers.
    - start_date, end_date (str): Start and end dates in the format 'YYYY-MM-DD'.
    
    Returns:
    - returns_df (pd.DataFrame): A DataFrame with dates as indexes, and columns corresponding
                                 to the log returns series of each ticker.
    '''

    # initialise output dataframe
    close_df = pd.DataFrame()
    
    for ticker in tickers:
        # retrieve stock data (includes Date, OHLC, Volume, Adjusted Close)
        format='%Y-%m-%d'
        s = yf.download(ticker, dt.datetime.strptime(start_date, format), dt.datetime.strptime(end_date, format))
        # append to returns_df
        close_df[ticker] = s['Adj Close']
        
    return close_df.dropna()