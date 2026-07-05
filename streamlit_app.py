import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

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
                    df = yf.download(ticker, period="6mo", progress=False)
                    if not df.empty:
                        # Technical Analysis Calculations
                        df.ta.rsi(length=14, append=True)
                        df.ta.sma(length=50, append=True)
                        df.ta.sma(length=200, append=True)
                        
                        latest = df.iloc[-1]
                        st.write(f"**Latest Price:** ₹{latest['Close']:.2f}")
                        st.line_chart(df[['Close', 'SMA_50', 'SMA_200']])
                        
                        # Technical Summary
                        rsi_val = latest['RSI_14']
                        st.write(f"**RSI (14):** {rsi_val:.2f} | **Status:** {'Overbought' if rsi_val > 70 else 'Oversold' if rsi_val < 30 else 'Neutral'}")
                        st.write(f"**SMA 50:** {latest['SMA_50']:.2f} | **SMA 200:** {latest['SMA_200']:.2f}")
                    else:
                        st.warning("No data found.")
                except Exception as e:
                    st.error(f"Error calculating indicators: {e}")
