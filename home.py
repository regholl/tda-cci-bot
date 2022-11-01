# Import required packages

from dash import html, dcc
import dash_bootstrap_components as dbc
from db import *
import plotly.graph_objects as go
import ta
from tda import *

# Define chart function

def update_candlestick(timeframe, ticker, cciLength, cciAvgLength, over_sold, over_bought):
    useEpoch = False
    if "m" in timeframe:
        frequencyType = "minute"
        frequency = int(timeframe.replace("m",""))
        periodType = "day"
        period = 2
    elif "h" in timeframe:
        frequencyType = "minute"
        frequency = np.round(int(timeframe.replace("h","")) * 60, 0)
        if frequency < 3 * 60:
            periodType = "day"
            period = 10
        else:
            periodType = None
            period = None
            useEpoch = True
    elif "D" in timeframe:
        frequencyType = "daily"
        frequency = 1
        periodType = "month"
        period = 3
    data = get_data_tda(ticker=ticker, periodType=periodType, period=period, frequencyType=frequencyType, frequency=frequency, useEpoch=useEpoch)
    df = pd.DataFrame()
    if frequencyType == "minute":
        time_format = "%m/%d %H:%M"
    elif frequencyType == "daily":
        time_format = "%m/%d"
    elif frequencyType == "weekly":
        time_format = "%m/%d/%Y"
    elif frequencyType == "monthly":
        time_format = "%b %Y"
    tda_times = [candle['datetime'] for candle in data]
    tda_dates = [dt.datetime.utcfromtimestamp(time_ / 1000) for time_ in tda_times]
    tda_locals = [utc.localize(date).astimezone(local_timezone) for date in tda_dates]
    tda_datetimes = [time_.strftime(time_format) for time_ in tda_locals]
    tda_opens = [item['open'] for item in data]
    tda_highs = [item['high'] for item in data]
    tda_lows = [item['low'] for item in data]
    tda_closes = [item['close'] for item in data]
    df['datetime'] = tda_datetimes
    df['open'] = tda_opens
    df['high'] = tda_highs
    df['low'] = tda_lows
    df['close'] = tda_closes

    # Candlestick chart

    fig = go.Figure()
    blank = pd.Series(" ")
    fig.add_trace(go.Candlestick(
        x = pd.Series(pd.concat([df['datetime'], blank], ignore_index=True)),
        open = pd.Series(pd.concat([df['open'], blank], ignore_index=True)),
        high = pd.Series(pd.concat([df['high'], blank], ignore_index=True)),
        low = pd.Series(pd.concat([df['low'], blank], ignore_index=True)),
        close = pd.Series(pd.concat([df['close'], blank], ignore_index=True)),
        name = 'Candles',
    ))
    quote = get_quote_tda(ticker)
    last = str(np.round(float(quote[ticker]['lastPrice']), 2))
    if "." not in last:
        last = last + ".00"
    if len(last.split(".")[1]) == 1:
        last = last + "0"
    fig.update_layout(
        title = f'Plotly chart: {ticker} ({last}), {frequency} {frequencyType}',
        height = 700,
        yaxis_title = 'Price',
        xaxis_title = 'Datetime',
        plot_bgcolor = 'gainsboro'
    )
    fig.update_xaxes(
        rangeslider_visible=False,
        showgrid=False,
        tickprefix=" "
    )
    fig.update_yaxes(
        showgrid=False,
        ticksuffix=" "
    )

    # CCI chart

    CCI = ta.trend.cci(df['high'], df['low'], df['close'], window= cciLength)
    df['CCI'] = CCI
    CCIAvg = df['CCI'].rolling(window=cciAvgLength).mean()
    df['CCIAvg'] = CCIAvg
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x = df['datetime'],
        y = df['CCI'],
        name = "CCI"
    ))
    fig1.add_trace(go.Scatter(
        x = df['datetime'],
        y = df['CCIAvg'],
        name = "CCIAvg"
    ))
    fig1.add_trace(go.Scatter(
        x = df['datetime'],
        y = [over_bought] * len(df['datetime']),
        name = "over_bought",
        line = {"dash": "dash"}
    ))
    fig1.add_trace(go.Scatter(
        x = df['datetime'],
        y = [over_sold] * len(df['datetime']),
        name = "over_sold",
        line = {"dash": "dash"}
    ))
    fig1.update_layout(
        title = f'Plotly chart: CCI {cciLength} and CCIAvg {cciAvgLength}',
        height = 700,
        yaxis_title = 'Value',
        xaxis_title = 'Datetime',
        plot_bgcolor = 'gainsboro'
    )
    fig1.update_xaxes(
        rangeslider_visible=False,
        showgrid=False,
        tickprefix=" "
    )
    fig1.update_yaxes(
        showgrid=False,
        ticksuffix=" "
    )

    return fig, fig1

# Define page function

def serve_home():

    # Get settings

    deta = connect_db()
    db_settings = deta.Base("db_settings")
    test = db_settings.get("watchlist")
    if not test:
        create_database(db_settings, name="settings")
        time.sleep(2)
        deta = connect_db()
        db_settings = deta.Base("db_settings")
    ticker = db_settings.get("ticker")['value']
    watchlist = db_settings.get("watchlist")['value']
    timeframe = db_settings.get("timeframe")['value']
    shares = db_settings.get("shares")['value']
    cciLength = db_settings.get("cciLength")['value']
    cciAvgLength = db_settings.get("cciAvgLength")['value']
    over_sold = db_settings.get("over_sold")['value']
    over_bought = db_settings.get("over_bought")['value']

    figs = update_candlestick()
    fig1 = figs[0]
    fig2 = figs[1]

    # Get on/off

    db_config = deta.Base("db_config")
    bot_on = bool(db_config.get("BOT_ON")['value'])
    if bot_on:
        on_off = "On"
    else:
        on_off = "Off"

    # Get names

    names = get_watchlist_tda(result="names")

    # Get tickers

    symbols = get_watchlist_tda()
    if ticker not in symbols:
        symbols.append(ticker)

    # Set up app layout

    layout = html.Div(
        children = [
            html.Br(),
            dbc.Row(
                children =[
                    dbc.Col(
                        children = [
                            html.Label("Timeframe"),
                            dcc.Dropdown(
                                id = "timeframe_dropdown",
                                options = ["1m", "10m", "1h", "4h", "1D"],
                                value = timeframe
                            )
                        ],
                        width = {"size": 2, 'offset': 1}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("Ticker"),
                            dcc.Dropdown(
                                id = "ticker_dropdown",
                                options = symbols,
                                value = ticker
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("Watchlist"),
                            dcc.Dropdown(
                                id = "watchlist_dropdown",
                                options = names,
                                value = watchlist
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("Shares"),
                            dcc.Input(
                                id = "shares_input",
                                type = "number",
                                value = shares,
                                min = 1,
                                max = 99999
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("On/off"),
                            dcc.RadioItems(
                                id = "on_off",
                                options = ['On', 'Off'], 
                                value = on_off, 
                                inline = False
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    )
                ]
            ),
            html.Br(),
            dbc.Row(
                children = [
                    dbc.Col(
                        children = [
                            dcc.Graph(
                                id='candlestick_chart',
                                figure = fig1
                            )
                        ],
                        width = {"size": 10, 'offset': 1}
                    )
                ]
            ),
            html.Br(),
            dbc.Row(
                children =[
                    dbc.Col(
                        children = [
                            html.Label("cciLength"),
                            dcc.Input(
                                id = "cciLength",
                                type = "number",
                                value = cciLength,
                                min = 1,
                                max = 99999
                            )
                        ],
                        width = {"size": 2, 'offset': 1}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("cciAvgLength"),
                            dcc.Input(
                                id = "cciAvgLength",
                                type = "number",
                                value = cciAvgLength,
                                min = -10000,
                                max = 10000
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("over_sold"),
                            dcc.Input(
                                id = "over_sold",
                                type = "number",
                                value = over_sold,
                                min = -10000,
                                max = 10000
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    ),
                    dbc.Col(
                        children = [
                            html.Label("over_bought"),
                            dcc.Input(
                                id = "over_bought",
                                type = "number",
                                value = over_bought,
                                min = 1,
                                max = 99999
                            )
                        ],
                        width = {"size": 2, 'offset': 0}
                    )
                ]
            ),
            html.Br(),
            dbc.Row(
                children = [
                    dbc.Col(
                        children = [
                            dcc.Graph(
                                id = 'cci_chart',
                                figure = fig2
                            )
                        ],
                        width = {"size": 10, 'offset': 1}
                    )
                ]
            ),
            html.Br()
        ]
    )
    return layout