# Import required packages

from dash import html
import dash_bootstrap_components as dbc
from db import *
from tda import *

# Define page function

def serve_positions():

    # Fetch positions

    positions = get_positions_tda()

    # Create table

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Symbol"), 
                    html.Th("Quantity"),
                    html.Th("Average Price"), 
                    html.Th("Market Value")
                ]
            )
        )
    ]
    rows = []
    for position in positions:
        symbol = position["instrument"]["symbol"]
        qty = max(int(position["longQuantity"]), int(position["shortQuantity"]))
        avg_p = np.round(float(position["averagePrice"]), 2)
        mv = np.round(float(position["marketValue"]), 2)
        row = html.Tr(
            [
                html.Td(symbol), 
                html.Td(qty),
                html.Td(avg_p),
                html.Td(mv)
            ]
        )
        rows.append(row)
    table_body = [html.Tbody(rows)]

    # Define page layout

    layout = html.Div(
        children = [
            html.Br(),
            dbc.Row(
                children = [
                    dbc.Col(
                        children = [
                            dbc.Table(
                                table_header + table_body, 
                                bordered=True,
                                dark=True,
                                hover=True,
                                responsive=True,
                                striped=True
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