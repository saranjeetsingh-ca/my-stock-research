import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta_py import rsi, sma, macd

# 1. Setup and Data Fetching
st.set_page_config(page_title="Pocket Research Pro", layout="wide")
st.title("📈 Pocket Research Tool")

@st.cache_data
def get_nse_instruments():
    url = "https://images.dhan.co/api-data/api-scrip-master.csv"
    df = pd.read_csv(url)
    nse_df = df[(df['SEM_EXM_EXCH_ID'] == 'NSE') & (df['SEM_SEGMENT'] == 'E')].copy()
    nse_df['yfinance_ticker'] = nse_df['SEM_TRADING_SYMBOL'] + '.NS'
    return nse_df

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker):
    data = yf.download(ticker, period="1y", progress=False)
    if not data.empty:
        # Flatten MultiIndex columns
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    return data

def pad_indicator(indicator_values, total_length):
    diff = total_length - len(indicator_values)
    return [np.nan] * diff + indicator_values

# Initialize instruments_df globally
instruments_df = get_nse_instruments()

# 2. Sidebar - Manual Selection
st.sidebar.header("Filter Scrips")
stock_options = instruments_df['SEM_CUSTOM_SYMBOL'].dropna().astype(str).tolist()
selected_names = st.sidebar.multiselect("Select Stocks to Analyze:", options=stock_options)

# 3. Sidebar - Scanner
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Quick Scanner")
if st.sidebar.button("Run Bullish Scanner"):
    with st.spinner("Scanning NSE stocks..."):
        bullish_list = []
        # Scanning first 20 for performance
        for _, row in instruments_df.head(20).iterrows():
            ticker = row['yfinance_ticker']
            data = fetch_stock_data(ticker)
            if not data.empty:
                close = data['Close'].squeeze().tolist()
                sma_200 = sma(close, 200)[-1]
                if data['Close'].iloc[-1] > sma_200:
                    bullish_list.append(row['SEM_CUSTOM_SYMBOL'])
        
        st.sidebar.write("### 🟢 Bullish (Above SMA 200)")
        st.sidebar.write(bullish_list)

# 4. Main Analysis Logic
if selected_names:
    for name in selected_names:
        row = instruments_df[instruments_df['SEM_CUSTOM_SYMBOL'] == name]
        if not row.empty:
            ticker = row.iloc[0]['yfinance_ticker']
            with st.expander(f"Analysis for {name}", expanded=False):
                df = fetch_stock_data(ticker)
                if not df.empty:
                    close = df['Close'].squeeze().tolist()
                    df['RSI_14'] = pad_indicator(rsi(close, 14), len(df))
                    df['SMA_50'] = pad_indicator(sma(close, 50), len(df))
                    df['SMA_200'] = pad_indicator(sma(close, 200), len(df))
                    df['MACD'] = pad_indicator(macd(close, 12, 26, 9), len(df))
                    
                    latest = df.iloc[-1]
                    st.write(f"**Latest Price:** ₹{float(latest['Close']):.2f}")
                    st.line_chart(df[['Close', 'SMA_50', 'SMA_200']])
                    
                    st.write("### 🔍 Signals")
                    col1, col2 = st.columns(2)
                    with col1:
                        if latest['Close'] > latest['SMA_50'] and latest['Close'] > latest['SMA_200']:
                            st.success("Trend: Bullish")
                        else:
                            st.warning("Trend: Neutral/Bearish")
                    with col2:
                        st.write(f"**RSI (14):** {latest['RSI_14']:.2f}")
                        st.write(f"**MACD:** {latest['MACD']:.2f}")
