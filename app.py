# Import required packages

from home import serve_home
from orders import serve_orders
from positions import serve_positions
from dash import Dash, dcc, html, exceptions
import dash_auth
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import datetime as dt
from db import *
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import ta
from tda import *
import time

# Create app

bs = "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css"
app = Dash(
    __name__, 
    suppress_callback_exceptions = True,
    meta_tags = [
        {
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1.0'
        }
    ],
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
app.title = "TDA CCI Bot"
server = app.server

def serve_layout():

    # Fetch user login database

    deta = connect_db()
    db_users = deta.Base("db_users")
    items = db_users.fetch().items
    if items == []:
        create_database(db_users, name="users")
        time.sleep(2)
        deta = connect_db()
        db_users = deta.Base("db_users")
        items = db_users.fetch().items
    users_dict = {}
    for item in items:
        users_dict[item['key']] = item['value']

    # Setup authentication system

    auth = dash_auth.BasicAuth(app, users_dict)

    # Define the base app layout 

    layout = html.Div(
        id = "main_page",
        children = [
            dcc.Location(
                id = 'url',
                refresh = False
            ),
            dbc.NavbarSimple(
                children = [
                    dbc.NavItem(dbc.NavLink("Home", href="/home")),
                    dbc.NavItem(dbc.NavLink("Orders", href="/orders")),
                    dbc.NavItem(dbc.NavLink("Positions", href="/positions"))
                ],
                brand = "TDA CCI Bot",
                brand_href = "#",
                color = "dark",
                dark = True,
            ),
            html.Div(
                id = 'page-content', 
                children = []
            )
        ],
        style = {
            "background-color": "gainsboro"
        }
    )
    return layout

app.layout = serve_layout

# Define the multi-page callback function

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == "/home":
        return serve_home()
    elif pathname == "/orders":
        return serve_orders()
    elif pathname == "/positions":
        return serve_positions()
    else:
        return serve_home()

# Callback function for timeframe on home.py

@app.callback(
    Output(component_id='timeframe_dropdown', component_property='value'),
    Input(component_id='timeframe_dropdown', component_property='value'),
    prevent_initial_callbacks = False
)
def update_timeframe(selected_timeframe):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_timeframe}, key="timeframe")
    raise exceptions.PreventUpdate

# Callback function for ticker on home.py

@app.callback(
    Output(component_id='ticker_dropdown', component_property='value'),
    Input(component_id='ticker_dropdown', component_property='value'),
    prevent_initial_callbacks = False
)
def update_ticker(selected_ticker):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_ticker}, key="ticker")
    raise exceptions.PreventUpdate

# Callback function for watchlist on home.py

@app.callback(
    Output(component_id='ticker_dropdown', component_property='options'),
    [Input(component_id='watchlist_dropdown', component_property='value'),
    Input(component_id='ticker_dropdown', component_property='value')],
    prevent_initial_callbacks = False
)
def update_watchlist(selected_watchlist, selected_ticker):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_watchlist}, key="watchlist")
    symbols = get_watchlist_tda(name=selected_watchlist)
    if selected_ticker not in symbols:
        symbols.append(selected_ticker)
    return symbols

# Callback function for shares on home.py

@app.callback(
    Output(component_id='shares_input', component_property='value'),
    Input(component_id='shares_input', component_property='value'),
    prevent_initial_callbacks = False
)
def update_shares(selected_shares):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_shares}, key="shares")
    raise exceptions.PreventUpdate

# Callback function for on/off on home.py

@app.callback(
    Output(component_id='on_off', component_property='value'),
    Input(component_id='on_off', component_property='value'),
    prevent_initial_callbacks = False
)
def update_onoff(selected_onoff):
    deta = connect_db()
    db_config = deta.Base("db_config")
    if selected_onoff == "On":
        bot_on = True
    elif selected_onoff == "Off":
        bot_on = False
    else:
        print("Error: Bot neither on nor off")
    db_config.update({"value": bot_on}, key="BOT_ON")
    raise exceptions.PreventUpdate

# Callback function for cciLength on home.py

@app.callback(
    Output(component_id='cciLength', component_property='value'),
    Input(component_id='cciLength', component_property='value'),
    prevent_initial_callbacks = False
)
def update_cciLength(selected_cciLength):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_cciLength}, key="cciLength")
    raise exceptions.PreventUpdate

# Callback function for cciAvgLength on home.py

@app.callback(
    Output(component_id='cciAvgLength', component_property='value'),
    Input(component_id='cciAvgLength', component_property='value'),
    prevent_initial_callbacks = False
)
def update_cciAvgLength(selected_cciAvgLength):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_cciAvgLength}, key="cciAvgLength")
    raise exceptions.PreventUpdate

# Callback function for over_sold on home.py

@app.callback(
    Output(component_id='over_sold', component_property='value'),
    Input(component_id='over_sold', component_property='value'),
    prevent_initial_callbacks = False
)
def update_over_sold(selected_over_sold):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_over_sold}, key="over_sold")
    raise exceptions.PreventUpdate

# Callback function for over_bought on home.py

@app.callback(
    Output(component_id='over_bought', component_property='value'),
    Input(component_id='over_bought', component_property='value'),
    prevent_initial_callbacks = False
)
def update_over_bought(selected_over_bought):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_over_bought}, key="over_bought")
    raise exceptions.PreventUpdate

# Callback function for chart on home.py

@app.callback(
    [Output(component_id='candlestick_chart', component_property='figure'),
    Output(component_id='cci_chart', component_property='figure')],
    [Input(component_id='timeframe_dropdown', component_property='value'),
    Input(component_id='ticker_dropdown', component_property='value'),
    Input(component_id='cciLength', component_property='value'),
    Input(component_id='cciAvgLength', component_property='value'),
    Input(component_id='over_sold', component_property='value'),
    Input(component_id='over_bought', component_property='value')]
)
def update_candlestick(selected_timeframe, selected_ticker, cciLength, cciAvgLength, over_sold, over_bought):
    # deta = connect_db()
    # db_config = deta.Base("db_config")
    useEpoch = False
    if "m" in selected_timeframe:
        frequencyType = "minute"
        frequency = int(selected_timeframe.replace("m",""))
        periodType = "day"
        period = 2
    elif "h" in selected_timeframe:
        frequencyType = "minute"
        frequency = np.round(int(selected_timeframe.replace("h","")) * 60, 0)
        if frequency < 3 * 60:
            periodType = "day"
            period = 10
        else:
            periodType = None
            period = None
            useEpoch = True
    elif "D" in selected_timeframe:
        frequencyType = "daily"
        frequency = 1
        periodType = "month"
        period = 3
    data = get_data_tda(ticker=selected_ticker, periodType=periodType, period=period, frequencyType=frequencyType, frequency=frequency, useEpoch=useEpoch)
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
    quote = get_quote_tda(selected_ticker)
    last = str(np.round(float(quote[selected_ticker]['lastPrice']), 2))
    if "." not in last:
        last = last + ".00"
    if len(last.split(".")[1]) == 1:
        last = last + "0"
    fig.update_layout(
        title = f'Plotly chart: {selected_ticker} ({last}), {frequency} {frequencyType}',
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

# Run the app

if __name__ == '__main__':
    app.run_server(port=8080, debug=False)