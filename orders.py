# Import required packages

from dash import html
import dash_bootstrap_components as dbc
from db import *
from tda import *

# Define page function

def serve_orders():

    # Fetch orders

    orders = get_orders2_tda()

    # Create table

    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Datetime"), 
                    html.Th("Symbol"),
                    html.Th("Side"), 
                    html.Th("Quantity")
                ]
            )
        )
    ]
    rows = []
    for order in orders:
        if "orderDate" in list(order.keys()):
            date1 = order["orderDate"]
        elif "transactionDate" in list(order.keys()):
            date1 = order["transactionDate"]
        else:
            print("Error: No order date found")
        dtm = pd.Timestamp(date1, tz=utc).astimezone(local_timezone).strftime("%m/%d/%Y %X")
        symbol = order["transactionItem"]["instrument"]["symbol"]
        side = order["transactionItem"]["instruction"]
        qty = int(order["transactionItem"]["amount"])
        price = np.round(float(order["transactionItem"]["price"]), 2)
        row = html.Tr(
            [
                html.Td(dtm), 
                html.Td(symbol),
                html.Td(side),
                html.Td(qty),
                html.Td(price)
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