# Import required packages

from dash import html, dcc
import dash_bootstrap_components as dbc
from db import *
from tda import *

# Define page functino

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
                            dcc.Graph(id='candlestick_chart')
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
                            dcc.Graph(id='cci_chart')
                        ],
                        width = {"size": 10, 'offset': 1}
                    )
                ]
            ),
            html.Br()
        ]
    )
    return layout