# Import required packages

from dash import Dash, dcc, html, exceptions
import dash_auth
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from db import *
from tda import *
import time

# Import other pages

from home import *
from orders import *
from positions import *

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
                refresh = True
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
            ),
            dcc.Interval(
                id = "interval",
                interval = 60 * 1000,
                n_intervals = 0
            )
        ],
        style = {
            "background-color": "gainsboro"
        }
    )
    return layout

app.layout = serve_layout

# Define the multi-page callback function

@app.callback(
    Output(component_id='page-content', component_property='children'),
    [Input(component_id='url', component_property='pathname'),
    Input(component_id='interval', component_property='n_intervals')],
    prevent_initial_callbacks=False
)
def display_page(pathname, n_intervals):
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
def update_timeframe(timeframe):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": timeframe}, key="timeframe")
    raise exceptions.PreventUpdate

# Callback function for ticker on home.py

@app.callback(
    Output(component_id='ticker_dropdown', component_property='value'),
    Input(component_id='ticker_dropdown', component_property='value'),
    prevent_initial_callbacks = False
)
def update_ticker(ticker):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": ticker}, key="ticker")
    raise exceptions.PreventUpdate

# Callback function for watchlist on home.py

@app.callback(
    Output(component_id='ticker_dropdown', component_property='options'),
    [Input(component_id='watchlist_dropdown', component_property='value'),
    Input(component_id='ticker_dropdown', component_property='value')],
    prevent_initial_callbacks = False
)
def update_watchlist(selected_watchlist, ticker):
    deta = connect_db()
    db_config = deta.Base("db_settings")
    db_config.update({"value": selected_watchlist}, key="watchlist")
    symbols = get_watchlist_tda(name=selected_watchlist)
    if ticker not in symbols:
        symbols.append(ticker)
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
def candlestick_callback(timeframe, ticker, cciLength, cciAvgLength, over_sold, over_bought):
    figs = update_candlestick(timeframe, ticker, cciLength, cciAvgLength, over_sold, over_bought)
    fig1 = figs[0]
    fig2 = figs[1]
    return fig1, fig2

# Run the app

if __name__ == '__main__':
    app.run(port=8080)