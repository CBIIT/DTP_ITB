import dash
from dash import html, dcc

dash.register_page(__name__, path='/tgi')

layout = html.Div(children=[
    html.H1(children='This is our Home page'),

    html.Div(children='''
        This is our TGI page content.
    ''')
])