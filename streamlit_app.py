import streamlit as st
import yfinance as yf
import pandas as pd
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
                    # Download data
                    data = yf.download(ticker, period="6mo", progress=False)
                    
                    # FIX: Check if data is valid before creating 'df'
                    if not data.empty:
                        df = data.copy() # Now 'df' is defined safely
                        
                        # Calculate indicators
                        # Note: ta-py expects lists
                        close_prices = df['Close'].squeeze().tolist()
                        df['RSI_14'] = rsi(close_prices, 14)
                        df['SMA_50'] = sma(close_prices, 50)
                        df['SMA_200'] = sma(close_prices, 200)
                        
                        latest = df.iloc[-1]
                        st.write(f"**Latest Price:** ₹{latest['Close']:.2f}")
                        st.line_chart(df[['Close', 'SMA_50', 'SMA_200']])
                        
                        rsi_val = latest['RSI_14']
                        st.write(f"**RSI (14):** {rsi_val:.2f}")
                    else:
                        st.warning("No data found for this ticker.")
                except Exception as e:
                    st.error(f"Error calculating indicators: {e}")
