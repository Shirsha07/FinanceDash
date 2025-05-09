import streamlit as st

# --- PAGE SETUP ---

page_price = st.Page(
    "views/Page_price.py",
    title="Stock Market",
    icon=":material/stacked_line_chart:",  # from Material Design by Google
    default=True,
)

pg = st.navigation(pages=[page_price])

# --- SHARED ON ALL PAGES ---
st.logo("imgs/logo_friendly.png", size="large")

# --- RUN NAVIGATION ---
pg.run()
