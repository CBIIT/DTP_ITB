import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/')

layout = dbc.Row(
    [
        dbc.Col(width=12)
    ]
)
