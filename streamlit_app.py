import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from ta_py import rsi, sma, macd

# ... (keep your existing setup and fetch functions)

# 5. New Scanner Feature
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Quick Scanner")
if st.sidebar.button("Run Bullish Scanner"):
    with st.spinner("Scanning NSE stocks..."):
        bullish_list = []
        # We limit to first 20 for speed in the browser
        for ticker in instruments_df['yfinance_ticker'].head(20): 
            data = fetch_stock_data(ticker)
            if not data.empty:
                data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
                close = data['Close'].squeeze().tolist()
                sma_200 = sma(close, 200)[-1]
                if data['Close'].iloc[-1] > sma_200:
                    bullish_list.append(ticker)
        
        st.write("### 🟢 Bullish Stocks (Above SMA 200)")
        st.write(bullish_list)
