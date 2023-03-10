import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from .dataservice import DataService
import dash_bio as dashbio

dash.register_page(__name__, path='/compounds')
dataService = DataService()

ROW_PADDING = {
        "paddingTop":"calc(var(--bs-gutter-x) * .5)",
        "paddingBottom":"calc(var(--bs-gutter-x) * .5)"
    }

layout = html.Div([
    dashbio.Jsme(
        smiles='O=C(Nc1cccc(Cl)c1)c3cncc4nnc(c2ccc(OC(F)F)cc2)n34',
    ),
])