# Import required packages

from dash import Dash
import dash_bootstrap_components as dbc

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