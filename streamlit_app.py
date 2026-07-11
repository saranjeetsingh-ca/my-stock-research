import streamlit as st
import feedparser
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re
import requests

# Download the VADER lexicon dictionary silently
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

# 1. UI Configuration
st.set_page_config(page_title="NLP Discovery Engine", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    h1 { font-size: 26px !important; text-align: center; color: #1E3A8A; font-weight: bold; margin-bottom: 5px; }
    p.sub { text-align: center; font-size: 13px; color: #6B7280; margin-bottom: 25px; }
    div.stButton > button {
        width: 100%; background-color: #10B981; color: white;
        font-weight: bold; padding: 12px; border-radius: 8px; font-size: 16px; border: none;
    }
    div.stButton > button:hover { background-color: #059669; color: white; }
    .stDataFrame div { font-size: 12px !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚡ Open-Universe NLP Catalyst Engine</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub'>Dynamic Nifty 500 Directory Ingestion • Open NLP Text Parsing • Actionable Signals Matrix</p>", unsafe_allow_html=True)

# 2. Dynamic Universe Ingestion (Nifty 500)
@st.cache_data(ttl=86400) # Cache the 500 stock directory for 24 hours
def load_nifty_500_universe():
    """Fetches the Nifty 500 master list and compiles a clean text-matching array."""
    # Using a reliable public GitHub mirror to bypass NSE server anti-bot firewalls
    url = "https://raw.githubusercontent.com/anirbanghoshsbi/NSE-Indices/master/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Failed to ingest Nifty 500 Master Directory: {e}")
        return {}

    universe = {}
    
    # Text suffixes to strip out so we match raw company tokens accurately
    noise_words = [
        r"\bltd\b", r"\blimited\b", r"\bindia\b", r"\bindustries\b", 
        r"\bcorp\b", r"\bcorporation\b", r"\benterprises\b"
    ]
    suffix_pattern = re.compile("|".join(noise_words), re.IGNORECASE)

    for _, row in df.iterrows():
        symbol = str(row['Symbol']).strip()
        company_name = str(row['Company Name']).lower()
        
        # Clean corporate legal noise (e.g., "Tata Motors Ltd." -> "tata motors")
        clean_name = suffix_pattern.sub("", company_name).strip()
        # Strip out excessive generic punctuation
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        
        # Scenario A: The news article uses the exact stock ticker (e.g., "HUDCO drops 3%")
        universe[rf"\b{symbol.lower()}\b"] = symbol
        
        # Scenario B: The news article uses the common company name (e.g., "Zomato signs pact")
        if len(clean_name) > 3: # Ignore ultra-short corrupted tokens
            universe[rf"\b{clean_name}\b"] = symbol
            
    return universe

# 3. Aggregated Broad Financial RSS Firehose Streams
RSS_FEEDS = {
    "Google Corporate News Pipeline": "https://news.google.com/rss/search?q=corporate+earnings+contracts+NSE+India&hl=en-IN&gl=IN&ceid=IN:en",
    "Google Financial Streams": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en"
}

def extract_ticker_nlp(headline, universe_map):
    """Scans raw headline tokens against all Nifty 500 lookup entities simultaneously."""
    headline_clean = headline.lower()
    for regex_pattern, ticker in universe_map.items():
        if re.search(regex_pattern, headline_clean):
            return ticker
    return None

@st.cache_data(ttl=300) # Cache live results for 5 minutes to avoid flooding RSS endpoints
def pipeline_processing_stream(universe_map, earnings_w, orders_w, legal_w, noise_th):
    sia = SentimentIntensityAnalyzer()
    detected_movers = []
    seen_headlines = set()
    now_utc = datetime.now(timezone.utc)
    
    for stream_name, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            title = str(entry.title)
            
            # Global deduplication filter
            if title.lower() in seen_headlines:
                continue
            seen_headlines.add(title.lower())
            
            # --- STAGE 1: OPEN ENTITY EXTRACTION ---
            matched_ticker = extract_ticker_nlp(title, universe_map)
            if not matched_ticker:
                continue # Discard macro noise stories not mentioning any Nifty 500 company
                
            # --- STAGE 2: RELATIVE TIME SHORTHAND ---
            try:
                pub_dt_utc = parsedate_to_datetime(entry.published)
                age_seconds = int((now_utc - pub_dt_utc).total_seconds())
                
                # Filter out anything stale (older than 48 hours)
                if age_seconds > 172800:
                    continue
                    
                if age_seconds < 0: age_str = "Just now"
                elif age_seconds < 3600: age_str = f"{age_seconds // 60}m ago"
                elif age_seconds < 86400: age_str = f"{age_seconds // 3600}h ago"
                else: age_str = f"{age_seconds // 86400}d ago"
            except:
                age_str = "Recent"
                
            # --- STAGE 3: SENTIMENT & EVENT WEIGHTING PIPELINE ---
            base_scores = sia.polarity_scores(title)
            score = base_scores['compound']
            
            # Custom Catalyst Modifiers
            category = "General News"
            title_lower = title.lower()
            
            if any(k in title_lower for k in ["q1", "q2", "q3", "q4", "profit", "earnings", "revenue"]):
                score *= earnings_w
                category = "📈 Corporate Performance"
            elif any(k in title_lower for k in ["order", "bagged", "won", "contract", "mou", "deal"]):
                score *= orders_w
                category = "💼 Order Acquisition"
            elif any(k in title_lower for k in ["tax", "fine", "notice", "fraud", "probe", "court", "cbi", "sebi"]):
                score *= legal_w
                category = "🚨 Regulatory / Legal"
                
            # --- STAGE 4: MACRO NOISE THRESHOLD FILTER ---
            # If the calculated absolute trading impact is minor, throw it out
            if abs(score) < noise_th:
                continue
                
            vector_label = "🟢 Bullish Vector" if score > 0 else "🔴 Bearish Vector"
            
            detected_movers.append({
                "Age": age_str,
                "Symbol": matched_ticker,
                "Catalyst Category": category,
                "Direction": vector_label,
                "Impact Score": round(score, 2),
                "Headline Intelligence": title
            })
            
    df = pd.DataFrame(detected_movers)
    if not df.empty:
        # Sort matrix to prioritize the highest absolute momentum impacts at the top
        df['AbsScore'] = df['Impact Score'].abs()
        df = df.sort_values(by='AbsScore', ascending=False).drop(columns=['AbsScore'])
        return df
    return pd.DataFrame()

# 4. User Interface Control Systems
st.sidebar.markdown("### 🎛️ Catalyst Tuning Parameters")
st.sidebar.caption("Adjust weighting multipliers for automated structural news categorization:")

earnings_multiplier = st.sidebar.slider("Earnings Surprise Weight", 0.5, 3.0, 1.5, 0.1)
orders_multiplier = st.sidebar.slider("Order Wins Weight", 0.5, 3.0, 1.8, 0.1)
legal_multiplier = st.sidebar.slider("Regulatory/Legal Impact Weight", 0.5, 3.0, 2.0, 0.1)

st.sidebar.markdown("---")
noise_threshold = st.sidebar.slider("Macro Noise Filter Cutoff", 0.0, 0.5, 0.15, 0.05)
st.sidebar.caption("Headlines with absolute scores below this value are filtered out as generic industry noise.")

# Initialize the dynamic open universe layout
with st.spinner("Compiling Nifty 500 Dynamic NLP Target Matrices..."):
    nifty_universe = load_nifty_500_universe()

if nifty_universe:
    st.info(f"NLP Target Arrays Loaded Successfully. Monitoring {len(nifty_universe)} unique Nifty corporate text patterns.")
    
    if st.button("📡 Deploy Stream Parsers & Intercept Market Catalysts", type="primary"):
        with st.spinner("Processing live financial media streams through the NLP architecture..."):
            signals_df = pipeline_processing_stream(
                nifty_universe, 
                earnings_multiplier, 
                orders_multiplier, 
                legal_multiplier, 
                noise_threshold
            )
            
            if not signals_df.empty:
                st.markdown("### 🎯 Live High-Conviction Actionable Signals Directory")
                st.caption("The system has matched raw unstructured streams against the Nifty 500 universe and calculated the following directional impact variables:")
                
                # Format dataframe layout for full visibility
                st.dataframe(
                    signals_df[["Age", "Symbol", "Catalyst Category", "Direction", "Impact Score", "Headline Intelligence"]],
                    use_container_width=True,
                    hide_index=True
                )
                st.success(f"Processing Complete. Isolated {len(signals_df)} validated company-level catalysts.")
            else:
                st.warning("No high-impact company-specific news breached the current filter threshold. Try softening the Macro Noise Filter Cutoff in the sidebar.")
