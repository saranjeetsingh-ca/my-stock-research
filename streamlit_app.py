import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Setup
st.set_page_config(page_title="My Stock Tool", layout="wide")
st.title("📈 Pocket Stock Research")

# 2. Define the Watchlist (This is where you add/remove stocks)
# You can change the stocks in the list below anytime
default_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

st.sidebar.header("Settings")
selected_stocks = st.sidebar.multiselect(
    "Select Scrips to Analyze:",
    options=["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "WIPRO.NS", "SBIN.NS"],
    default=default_stocks
)

# 3. Analysis Logic
st.write(f"Analyzing: {', '.join(selected_stocks)}")

for ticker in selected_stocks:
    with st.expander(f"Analysis for {ticker}", expanded=False):
        try:
            # Fetch data from Yahoo Finance
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            # Display basic price info
            latest_price = hist['Close'].iloc[-1]
            st.write(f"**Latest Price:** ₹{latest_price:.2f}")
            
            # Show a simple chart
            st.line_chart(hist['Close'])
            
            # Show some basic info
            info = stock.info
            st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
            st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
            
        except Exception as e:
            st.error(f"Could not fetch data for {ticker}. Error: {e}")
