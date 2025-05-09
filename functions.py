import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import random
from fp.fp import FreeProxy

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc

def get_proxy_dict(probability=0.5):
    if random.random() < probability:
        proxy = FreeProxy(rand=True).get()
        proxies_dict = {
            "http": proxy
        }
        return proxies_dict
    else:
        return None

@st.cache_data
def fetch_info(ticker):
    proxy = get_proxy_dict()
    # yf.set_config(proxy=proxy)
    ticker = yf.Ticker(ticker, proxy=proxy)
    try:
        info = ticker.info
        return info
        # if "quoteType" in ticker.info:
        #     return info
        # else:
        #     return None
    except Exception as e:
        return e

@st.cache_data
def fetch_history(ticker, period="3mo", interval="1d", start=None):
    proxy = get_proxy_dict()
    ticker = yf.Ticker(ticker, proxy=proxy)
    try:
        if start:
            hist = ticker.history(
                start=start,
                interval=interval
            )
        else:
            hist = ticker.history(
                period=period,
                interval=interval
            )

        return hist

    except Exception as e:
        return e

@st.cache_data
def fetch_splits(ticker):
    ticker = yf.Ticker(ticker)
    return ticker.splits

@st.cache_data
def fetch_table(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        proxy = FreeProxy().get()
        proxies_dict = {
            "http": proxy
        }
        response = requests.get(url, headers=headers, proxies=proxies_dict, timeout=5)
        df = pd.read_html(response.content)
        return df[0]
    except Exception as e:
        return e

def format_value(value):
    # Split the string at the first space
    base_value, change = value.split(' ', 1)

    # Determine the color based on the sign of the change
    if change.startswith('+'):
        color = 'green'
    else:
        color = 'red'

    # Create the formatted string
    return f"{base_value}<br><span style='color: {color};'>{change}</span>"

def remove_duplicates(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result

def top_table(df):
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='lightgrey',
                    align='center'),
        cells=dict(values=[df[col] for col in df.columns],
                   fill_color='white',
                   align=['left', 'right']),
        columnwidth=[0.6, 0.4]
    )])

    fig.update_layout(height=270, margin=dict(t=0, b=0, l=0, r=0))

    return fig


def info_table(info):
    data = {}

    TYPE = info['quoteType']

    if TYPE == "EQUITY":

        data['Quote Type'] = TYPE
        data['Name'] = info.get('shortName', "")
        data['Country'] = info.get('country', "")
        data['Market Exchange'] = info.get('exchange', "")
        data['Sector'] = info.get('sector', "")
        data['Industry'] = info.get('industry', "")
        data['Market Capitalization'] = str(info.get('marketCap', ""))
        data['Quote currency'] = info.get('currency', "?")
        data['Beta'] = str(info.get('beta', "?"))
        data['Price'] = info.get('currentPrice', 0)

    elif TYPE == "ETF":

        data['Quote Type'] = TYPE
        data['Market Exchange'] = info.get('exchange', "")
        data['Fund Family'] = info.get('fundFamily', "")
        data['Category'] = info.get('category', "")
        data['Total Assets'] = info.get('totalAssets', "")
        data['Quote currency'] = info.get('currency', "?")
        data['Beta'] = str(info.get('beta3Year', "?"))
        data['Price'] = info.get('navPrice', 0)

    elif TYPE == "INDEX":

        data['Quote Type'] = TYPE
        data['Market'] = info.get('market', "")
        data['Price'] = info.get('previousClose', 0)

    elif TYPE == "FUTURE":
        pass

    elif TYPE == "MUTUALFUND":
        pass

    elif TYPE == "CURRENCY":
        pass

    df = pd.DataFrame([data]).T

    return df

# ---- CHARTS ----
def plot_gauge(df, ticker):
    df = df[df['Ticker'] == ticker]

    initial_price = df['Close'].iloc[0]
    last_price = df['Close'].iloc[-1]
    last_pct = df['Pct_change'].iloc[-1] * 100
    color_pct = 'green' if last_pct > 0 else 'red'

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=last_pct,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': ticker},
        number={'font': {'color': color_pct}},
        gauge={
            'axis': {'range': [-50, 50]},
            'bar': {'thickness': 0},
            'steps': [
                {'range': [0, last_pct], 'color': color_pct, 'thickness': 0.8},
            ],
        },
    ))

    fig.update_layout(height=150, margin=dict(t=50, b=0, l=0, r=0))

    return fig

def plot_candles_stick_bar(df, title="", currency=""):

    rows = 1
    row_heights = [7]
    for col_name in df.columns:
        if col_name in ['Volume', 'MACD', 'ATR', 'RSI']:
            rows += 1
            row_heights.append(3)

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.01,
                        subplot_titles=None,
                        row_heights=row_heights
                        )

    fig.update_xaxes(title_text="Date", row=rows, col=1)

    row = 1
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'],
                                 name="OHVC",
                                 ),
                  row=1, col=1)

    for col_name in df.columns:

        if 'SMA' in col_name or 'EMA' in col_name:
            fig.add_trace(go.Scatter(x=df.index,
                                     y=df[col_name],
                                     mode='lines',
                                     line=dict(
                                         #color='black',
                                         width=2
                                     ),
                                     name=col_name),
                          row=1, col=1)

        elif 'Crossover' in col_name:

            first_period = col_name.split('_')[1].split('/')[0]

            for i, v in df[col_name].items():

                if v == 1.0:  # Buy signal

                    fig.add_annotation(x=df.index[i], y=df[f'SMA_{first_period}'][i],
                                       text="Golden cross",
                                       showarrow=True,
                                       arrowhead=1,
                                       arrowsize=1,
                                       ay=60
                                       )

                if v == -1.0:  # Sell signal

                    fig.add_annotation(x=df.index[i], y=df[f'SMA_{first_period}'][i],
                                       text="Death cross",
                                       showarrow=True,
                                       arrowhead=1,
                                       arrowsize=1,
                                       ay=-60
                                       )

        if col_name == 'Volume':
            row += 1

            volume_colors = ['green' if df['Close'].iloc[i] > df['Open'].iloc[i] else 'red' for i in range(len(df))]

            fig.add_trace(go.Bar(x=df.index,
                                 y=df[col_name],
                                 name=col_name,
                                 marker_color=volume_colors,
                                 hovertemplate=
                                 '%{x}<br>' +
                                 'Volume: %{y}<br>' +
                                 'ΔVolume: %{customdata[0]}<extra></extra>',
                                 customdata=df[["ΔVolume%"]].values
                                 ),
                          row=row, col=1)

            fig.update_yaxes(title_text="Volume", row=row, col=1)

        elif col_name == 'MACD':
            row += 1

            fig.add_trace(go.Scatter(x=df.index,
                                     y=df[col_name],
                                     name=col_name,
                                     ),
                          row=row, col=1)

            fig.update_yaxes(title_text="MACD", row=row, col=1)

            if 'Signal' in df.columns:
                fig.add_trace(go.Scatter(x=df.index,
                                         y=df['Signal'],
                                         name='Signal',
                                         ),
                              row=row, col=1)

            if 'MACD_Hist' in df.columns:
                MACD_colors = ['green' if df['MACD_Hist'][i] > 0 else 'red' for i in range(len(df))]

                fig.add_trace(go.Bar(x=df.index,
                                     y=df['MACD_Hist'],
                                     name='MACD_Hist',
                                     marker_color=MACD_colors),
                              row=row, col=1)

        elif col_name == 'ATR':
            row += 1

            fig.add_trace(go.Scatter(x=df.index,
                                     y=df[col_name],
                                     name=col_name,
                                     ),
                          row=row, col=1)

            fig.update_yaxes(title_text="ATR", row=row, col=1)

        elif col_name == 'RSI':
            row += 1

            fig.add_trace(go.Scatter(x=df.index,
                                     y=df[col_name],
                                     name=col_name,
                                     ),
                          row=row, col=1)

            fig.update_yaxes(title_text="RSI", row=row, col=1)

            fig.add_hline(y=70, line_dash="dash", annotation_text='top', row=row, col=1)
            fig.add_hline(y=30, line_dash="dash", annotation_text='bottom', row=row, col=1)
            fig.add_hrect(y0=30, y1=70, fillcolor="blue", opacity=0.25, line_width=0, row=row, col=1)

    fig.update_layout(
        title=title,
        # xaxis_title='Date',
        yaxis_title=f'Price (in {currency})',
        # xaxis2_title='Date',
        # yaxis2_title='Volume',
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",  # Aligns the legend vertically to the top
            y=-0.15,  # Positions the legend below the subplots
            xanchor="center",  # Aligns the legend horizontally to the center
            x=0.5  # Centers the legend horizontally
        ),
        showlegend=True,
        xaxis_rangeslider_visible=False,
        height=800
    )

    return fig


def plot_candles_stick(df, title="", time_span=None):

    fig = go.Figure()


    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'],
                                 name="OHVC")
                  )

    if 'SMA' in df.columns:
        fig.add_trace(go.Scatter(x=df.index,
                                 y=df['SMA'],
                                 mode='lines',
                                 line=dict(color='black', width=2),
                                 name=f'{time_span}SMA')
                      )
    if 'EMA' in df.columns:
        fig.add_trace(go.Scatter(x=df.index,
                                 y=df['EMA'],
                                 mode='lines',
                                 line=dict(color='blue', width=2),
                                 name=f'{time_span}EMA')
                      )

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",  # Aligns the legend vertically to the top
            y=-0.3,  # Positions the legend below the subplots
            xanchor="center",  # Aligns the legend horizontally to the center
            x=0.5  # Centers the legend horizontally
        ),
        showlegend=True,
        xaxis_rangeslider_visible=False,
    )

    return fig

def plot_line_multiple(df, title=""):
    fig = go.Figure()

    dfs = df.groupby('Ticker')

    for df_name, df in dfs:
        fig.add_trace(go.Scatter(x=df.index,
                                 y=df['Pct_change'],
                                 mode='lines',
                                 name=f'{df_name}',
                                 meta=df_name,
                                 hovertemplate='%{meta}: %{y:.2f}<br><extra></extra>', )
                      )

    fig.add_hline(y=0, line_dash="dash")

    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Percentage change',
        hovermode='x',
        xaxis=dict(
            showspikes=True,  # Enable vertical spikes
            spikemode='across',  # Draw spikes across the entire plot
            spikesnap='cursor',  # Snap spikes to the cursor position
            showline=True,  # Show axis line
            showgrid=True,  # Show grid lines
            spikecolor='black',  # Custom color for spikes
            spikethickness=1,  # Custom thickness for spikes
            rangeslider=dict(
                visible=True,
                thickness=0.1
            ),
        ),
        yaxis=dict(
            tickformat='.0%',
            showspikes=True,  # Enable horizontal spikes
            spikemode='across',  # Draw spikes across the entire plot
            spikesnap='cursor',  # Snap spikes to the cursor position
            showline=True,  # Show axis line
            showgrid=True,  # Show grid lines
            spikecolor='black',  # Custom color for spikes
            spikethickness=1,  # Custom thickness for spikes
            side='right'  # Move the y-axis ticks to the right side
        ),
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",  # Aligns the legend vertically to the top
            y=-0.3,  # Positions the legend below the subplots
            xanchor="center",  # Aligns the legend horizontally to the center
            x=0.5  # Centers the legend horizontally
        ),
        showlegend=True,
        # xaxis_rangeslider_visible=True,
        height=800
    )

    return fig

