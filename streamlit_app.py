import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta_py import rsi, sma

# 1. Page Setup
st.set_page_config(page_title="Pocket Research", layout="wide")
st.title("📈 Pocket Research Tool")

# 2. Fetch Master List from Dhan
@st.cache_data
def get_nse_instruments():
    url = "https://images.dhan.co/api-data/api-scrip-master.csv"
    df = pd.read_csv(url)
    nse_df = df[(df['SEM_EXM_EXCH_ID'] == 'NSE') & (df['SEM_SEGMENT'] == 'E')].copy()
    nse_df['yfinance_ticker'] = nse_df['SEM_TRADING_SYMBOL'] + '.NS'
    return nse_df

# Helper function to fix length mismatch
def pad_indicator(indicator_values, total_length):
    # If the indicator list is shorter, fill the beginning with NaNs
    diff = total_length - len(indicator_values)
    return [np.nan] * diff + indicator_values

instruments_df = get_nse_instruments()

# 3. Sidebar
st.sidebar.header("Filter Scrips")
stock_options = instruments_df['SEM_CUSTOM_SYMBOL'].dropna().astype(str).tolist()
selected_names = st.sidebar.multiselect("Select Stocks to Analyze:", options=stock_options)

# 4. Analysis
if selected_names:
    for name in selected_names:
        row = instruments_df[instruments_df['SEM_CUSTOM_SYMBOL'] == name]
        if not row.empty:
            ticker = row.iloc[0]['yfinance_ticker']
            
            with st.expander(f"Analysis for {name}", expanded=False):
                try:
                    data = yf.download(ticker, period="1y", progress=False)
                    if not data.empty:
                        df = data.copy()
                        close_prices = df['Close'].squeeze().tolist()
                        
                        # Apply indicators with padding
                        df['RSI_14'] = pad_indicator(rsi(close_prices, 14), len(df))
                        df['SMA_50'] = pad_indicator(sma(close_prices, 50), len(df))
                        df['SMA_200'] = pad_indicator(sma(close_prices, 200), len(df))
                        
                        latest = df.iloc[-1]
                        st.write(f"**Latest Price:** ₹{latest['Close']:.2f}")
                        st.line_chart(df[['Close', 'SMA_50', 'SMA_200']])
                        
                        st.write(f"**RSI (14):** {latest['RSI_14']:.2f}")
                    else:
                        st.warning("No data found.")
                except Exception as e:
                    st.error(f"Error: {e}")
