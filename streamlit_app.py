import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Page Setup
st.set_page_config(page_title="Pocket Research", layout="wide")
st.title("📈 Pocket Research Tool")

# 2. Fetch Master List from Dhan
@st.cache_data
def get_nse_instruments():
    url = "https://images.dhan.co/api-data/api-scrip-master.csv"
    df = pd.read_csv(url)
    # Filter for NSE Equity only
    nse_df = df[(df['SEM_EXM_EXCH_ID'] == 'NSE') & (df['SEM_SEGMENT'] == 'E')].copy()
    # yfinance needs the symbol with '.NS' appended
    nse_df['yfinance_ticker'] = nse_df['SEM_TRADING_SYMBOL'] + '.NS'
    return nse_df

# Load the data
instruments_df = get_nse_instruments()

# 3. Sidebar: Searchable Dropdown
st.sidebar.header("Filter Scrips")
st.sidebar.write(f"Available NSE Stocks: {len(instruments_df)}")

# Clean the list for the dropdown
stock_options = instruments_df['SEM_CUSTOM_SYMBOL'].dropna().astype(str).tolist()

# User selection (no default to prevent crashes)
selected_names = st.sidebar.multiselect(
    "Select Stocks to Analyze:",
    options=stock_options
)

# 4. Main Dashboard Analysis
if selected_names:
    for name in selected_names:
        # Get the row corresponding to the name
        row = instruments_df[instruments_df['SEM_CUSTOM_SYMBOL'] == name]
        if not row.empty:
            ticker = row.iloc[0]['yfinance_ticker']
            
            with st.expander(f"Analysis for {name} ({ticker})", expanded=False):
                try:
                    # Fetch Data
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="1mo")
                    
                    if not hist.empty:
                        st.write(f"**Latest Price:** ₹{hist['Close'].iloc[-1]:.2f}")
                        st.line_chart(hist['Close'])
                        
                        # Fetch and display info
                        info = stock.info
                        st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
                        st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                    else:
                        st.warning("No historical data found.")
                except Exception as e:
                    st.error(f"Error fetching data: {e}")
else:
    st.info("Use the sidebar to search and select stocks to begin your analysis.")
