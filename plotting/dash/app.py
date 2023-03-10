# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output, State
import dash
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    use_pages=True,
    title='DCTD Data Plots',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)



ROW_PADDING = {
        "paddingTop":"calc(var(--bs-gutter-x) * .5)",
        "paddingBottom":"calc(var(--bs-gutter-x) * .5)"
    }

#### NAV STUFF ###########
nav = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Home", active="exact", href="/")),
        dbc.NavItem(dbc.NavLink("Five Dose", active="exact",href="/fivedose")),
        dbc.NavItem(dbc.NavLink("One Dose", active="exact",href="/onedose")),
        dbc.NavItem(dbc.NavLink("Invivo", active="exact", href="/invivo")),
        dbc.NavItem(dbc.NavLink("Compounds", active="exact", href="/compounds"))
    ],
    pills=True,
    navbar=True
)

################################
# ++++++++++++++++ Application Layout +++++++++++++++
app.layout = dbc.Container(
        fluid=True,
        class_name='text-center',
        children=[
            dbc.Row(html.H1('DCTD Graphs and Plots')),
            dbc.Row(dbc.Col(dbc.Navbar(nav),width=12,id='nav-bar-col'),id='nav-bar-row'),
            dbc.Row(dbc.Col(dash.page_container,width=12),id='page-container-col')
        ]
    )
# +++++++++++++++++++++++++++++++++++++++++++++++++++



# ****************************************




# ********** Start The server Here **********
if __name__ == '__main__':
    app.run(debug=True)
# *******************************************