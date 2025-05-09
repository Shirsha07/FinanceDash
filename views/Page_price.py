from functions import *
from contact import contact_form
from streamlit_javascript import st_javascript
from zoneinfo import ZoneInfo
import yfinance as yf  # Import yfinance


@st.dialog("Contact Me")
def show_contact_form():
    contact_form()


st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon=":material/stacked_line_chart:",
    layout="wide",
)

# --- LOGO ---
st.html(
    """
  <style>
    [alt=Logo] {
      height: 3rem;
      width: auto;
      padding-left: 1rem;
    }
  </style>
"""
)

# --- TIME ZONE ---
if "timezone" not in st.session_state:
    timezone = st_javascript(
        """await (async () => {
                        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                        return userTimezone
                        })().then(returnValue => returnValue)"""
    )
    if isinstance(timezone, int):
        st.stop()
    st.session_state["timezone"] = ZoneInfo(timezone)


# --- SESSION STATE -----
all_my_widget_keys_to_keep = {
    "current_time_price_page": datetime.datetime.now(
        st.session_state["timezone"]
    ).replace(microsecond=0, tzinfo=None),
    "tickers": "TATAMOTORS.NS",  # Changed default to TATAMOTORS
    "dark_mode": False,
    "toggle_theme": False,
    "financial_period": "Annual",
}

for key in all_my_widget_keys_to_keep:
    if key not in st.session_state:
        st.session_state[key] = all_my_widget_keys_to_keep[key]

for key in all_my_widget_keys_to_keep:
    st.session_state[key] = st.session_state[key]


# --- SIDEBAR ---
with st.sidebar:
    TOGGLE_THEME = st.toggle(
        label="Dark mode :material/dark_mode:",
        key="toggle_theme",
        help="Switch to dark theme",
        # value=False
    )


    TICKERS = st.text_input(
        label="Securities:",
        # value='MSFT',
        key="tickers",
    )

    st.write("eg.: TATAMOTORS.NS, RELIANCE.NS, INFY.NS (max 10)")

    TICKERS = [item.strip() for item in TICKERS.split(",") if item.strip() != ""]

    TICKERS = remove_duplicates(TICKERS)

    if len(TICKERS) > 10:
        st.error("Only first 10 tickers are shown")
        TICKERS = TICKERS[:10]

    _tickers = list()
    for TICKER in TICKERS:
        info = fetch_info(TICKER)
        if isinstance(info, Exception):
            st.error(info)
            fetch_info.clear(TICKER)
        else:
            QUOTE_TYPE = info.get("quoteType", "")
            if QUOTE_TYPE not in ["EQUITY", "ETF", "INDEX"]:
                st.error(f"{TICKER} has an invalid quoteType ({QUOTE_TYPE})")
            else:
                _tickers.append(TICKER)

    TICKERS = _tickers

    period_list = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

    PERIOD = st.selectbox(
        label="Period",
        options=period_list,
        index=3,
        placeholder="Select period...",
    )

    interval_list = [
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
        "1h",
        "1d",
        "5d",
        "1wk",
        "1mo",
        "3mo",
    ]

    if PERIOD in interval_list:
        idx = interval_list.index(PERIOD)
        interval_list = interval_list[:idx]

    INTERVAL = st.selectbox(
        label="Interval",
        options=interval_list,
        index=len(interval_list) - 4,
        placeholder="Select interval...",
    )

    if len(TICKERS) == 1:

        TOGGLE_VOL = st.toggle(label="Volume", value=True)

        indicator_list = [
            "SMA_20",
            "SMA_50",
            "SMA_200",
            "EMA_20",
            "EMA_50",
            "EMA_200",
            "MACD",
            "RSI",
        ]

        INDICATORS = st.multiselect(
            label="Technical indicators:", options=indicator_list
        )

        if "SMA_X" in INDICATORS or "EMA_X" in INDICATORS:
            TIME_SPAN = st.slider(
                label="Select time span:",
                min_value=10,  # The minimum permitted value.
                max_value=200,  # The maximum permitted value.
                value=30,  # The value of the slider when it first renders.
            )
            INDICATORS = [
                indicator.replace("X", str(TIME_SPAN))
                if "_X" in indicator
                else indicator
                for indicator in INDICATORS
            ]

    st.write("")
    button = st.button("Refresh data")

    if button:
        st.session_state["current_time_price_page"] = datetime.datetime.now(
            st.session_state["timezone"]
        ).replace(microsecond=0, tzinfo=None)
        fetch_table.clear()
        fetch_info.clear()
        fetch_history.clear()
        # st.cache_data.clear()

    st.write("Last update:", st.session_state["current_time_price_page"])

    st.markdown("Made with ❤️ by Leonardo")

    button = st.button("✉️ Contact Me", key="contact")

    if button:
        show_contact_form()

    # ----CREDIT----
    st.write("")
    st.write("")
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown(
            "<p style='text-align: right;'>Powered by:</p>",
            unsafe_allow_html=True,
        )
    with col2:
        st.image("imgs/logo_yahoo_lightpurple.png", width=100)


# --- MAINPAGE ---
st.title("Stock Market Dashboard")

def display_indices():
    """Displays the performance of key global indices."""
    indices = ["^GSPC", "^DJI", "^IXIC", "^N225", "^GDAXI", "^NSEI"]  # Add NSEI
    indices_names = [
        "S&P 500",
        "Dow Jones",
        "NASDAQ",
        "Nikkei 225",
        "DAX",
        "NIFTY 50",
    ]

    try:
        indices_data = yf.download(indices, period="2d")  # Need 2 days to get change
        if not indices_data.empty:
            st.subheader("📊 Major Global Indices")
            latest_prices = indices_data["Close"].iloc[-1]
            previous_closes = indices_data["Close"].iloc[-2]
            changes = latest_prices - previous_closes
            percent_changes = (changes / previous_closes) * 100

            index_data = []
            for i, index in enumerate(indices):
                index_data.append(
                    {
                        "Index": indices_names[i],
                        "Price": f"{latest_prices[index]:.2f}",
                        "Change": f"{changes[index]:+.2f}",
                        "Change (%)": f"{percent_changes[index]:+.2f}%",
                    }
                )

            df_indices = pd.DataFrame(index_data)
            st.dataframe(df_indices, use_container_width=True)
        else:
            st.warning("No index data retrieved.")
    except Exception as e:
        st.error(f"Error fetching indices: {e}")

def display_top_movers(exchange="NSE"):
    """Displays the top 5 gainers and losers on the specified exchange."""
    try:
        if exchange == "NSE":
            gainers_url = "https://www.nseindia.com/live_market/dynaContent/live_analysis/nifty_top_gainers.htm"
            losers_url = "https://www.nseindia.com/live_market/dynaContent/live_analysis/nifty_top_losers.htm"
        elif exchange == "BSE":
            gainers_url = "https://www.bseindia.com/markets/equity/EQReports/topGainers.aspx"
            losers_url = "https://www.bseindia.com/markets/equity/EQReports/topLosers.aspx"
        else:
            st.error("Invalid exchange.  Choose NSE or BSE.")
            return

        # Fetch the tables
        gainers_df = fetch_table(gainers_url, 0)  # NSE and BSE gainers table is the first table
        losers_df = fetch_table(losers_url, 0)  # NSE and BSE losers table is the first table

        if not gainers_df.empty:
            if exchange == "NSE":
                gainers_df = gainers_df[["Symbol", "Last", "Change", "% Change"]]
                gainers_df.columns = ["Symbol", "Last Traded Price", "Change", "Change %"]
            elif exchange == "BSE":
                gainers_df = gainers_df[["Company", "Close", "Change", "%Change"]]
                gainers_df.columns = ["Symbol", "Last Traded Price", "Change", "Change %"]
            st.subheader(f"Top 5 Gainers ({exchange})")
            st.dataframe(
                gainers_df.head().style.format(
                    {
                        "Last Traded Price": "{:.2f}",
                        "Change": "{:.2f}",
                        "Change %": "{:.2f}%",
                    }
                ),
                use_container_width=True,
            )

        if not losers_df.empty:
            if exchange == "NSE":
                losers_df = losers_df[["Symbol", "Last", "Change", "% Change"]]
                losers_df.columns = ["Symbol", "Last Traded Price", "Change", "Change %"]
            elif exchange == "BSE":
                losers_df = losers_df[["Company", "Close", "Change", "%Change"]]
                losers_df.columns = ["Symbol", "Last Traded Price", "Change", "Change %"]
            st.subheader(f"Top 5 Losers ({exchange})")
            st.dataframe(
                losers_df.head().style.format(
                    {
                        "Last Traded Price": "{:.2f}",
                        "Change": "{:.2f}",
                        "Change %": "{:.2f}%",
                    }
                ),
                use_container_width=True,
            )
    except Exception as e:
        st.error(f"Error fetching top movers for {exchange}: {e}")



def display_security_info(ticker_symbol="TATAMOTORS.NS"):
    """Displays detailed information and a candlestick chart for a given security."""
    try:
        security = yf.Ticker(ticker_symbol)
        info = security.info
        if info:
            st.subheader(f"Security: {info['shortName']}")
            security_info_df = info_table(info)
            st.dataframe(security_info_df, use_container_width=True)

            # Fetch and display the price chart
            security_history = security.history(
                period="1y"
            )  # Example: 1-year history
            if not security_history.empty:
                fig = plot_candles_stick_bar(
                    security_history,
                    title=f"{info['shortName']} - 1 Year",
                    currency=info.get("currency", "INR"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(
                    f"Could not retrieve historical data for {ticker_symbol} for the chart."
                )
        else:
            st.error(f"Could not retrieve information for ticker: {ticker_symbol}")
    except Exception as e:
        st.error(f"Error fetching security information: {e}")



# --- Main function to run the app ---
def main():
    """Main function to run the Streamlit application."""
    display_indices()
    display_top_movers("NSE")  # Display NSE top movers
    display_top_movers("BSE")  # Display BSE Top movers
    display_security_info()  # Defaults to TATAMOTORS.NS


if __name__ == "__main__":
    main()


