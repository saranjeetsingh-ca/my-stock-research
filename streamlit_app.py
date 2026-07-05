import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Fetch Master List from Dhan
@st.cache_data
def get_nse_instruments():
    # Dhan's master CSV URL
    url = "https://images.dhan.co/api-data/api-scrip-master.csv"
    df = pd.read_csv(url)
    # Filter for NSE Equity only
    nse_df = df[(df['SEM_EXM_EXCH_ID'] == 'NSE') & (df['SEM_SEGMENT'] == 'E')].copy()
    
    # yfinance needs the symbol with '.NS' appended
    nse_df['yfinance_ticker'] = nse_df['SEM_TRADING_SYMBOL'] + '.NS'
    return nse_df

# Load the data
instruments_df = get_nse_instruments()

st.set_page_config(page_title="Pocket Research", layout="wide")
st.title("📈 Pocket Research Tool")

# 2. Sidebar: Searchable Dropdown
st.sidebar.header("Filter Scrips")
# Let the user pick by the "Custom Symbol" (e.g., RELIANCE)
selected_names = st.sidebar.multiselect(
    "Select Stocks to Analyze:",
    options=instruments_df['SEM_CUSTOM_SYMBOL'].tolist(),
    default=["RELIANCE", "TCS", "INFY"]
)

# 3. Main Dashboard Analysis
if selected_names:
    for name in selected_names:
        # Get the corresponding yfinance ticker
        row = instruments_df[instruments_df['SEM_CUSTOM_SYMBOL'] == name].iloc[0]
        ticker = row['yfinance_ticker']
        
        with st.expander(f"Analysis for {name} ({ticker})", expanded=False):
            try:
                # Fetch Data
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1mo")
                
                if not hist.empty:
                    st.write(f"**Latest Price:** ₹{hist['Close'].iloc[-1]:.2f}")
                    st.line_chart(hist['Close'])
                    
                    # Basic Financials
                    info = stock.info
                    st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
                    st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                else:
                    st.warning("No historical data found for this symbol.")
            except Exception as e:
                st.error(f"Error fetching data: {e}")
else:
    st.info("Select stocks from the sidebar to begin analysis.")
