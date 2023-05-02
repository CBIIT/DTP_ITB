import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from .dataservice import dataService

dash.register_page(__name__, path='/cells')

# nscs = dataService.COMP_NSCS

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}

left_select = dbc.Card(id='cells-sel-card', body=True, children=[
    html.Div(id='cells-input-form-div', children=[
        dbc.Form(id='cells-input-form', children=[
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select Cell Line", html_for="cells-dropdown"),
                    dcc.Dropdown(id="cells-dropdown")
                ])
            ], style=ROW_PADDING)
        ])
    ])
])


@dash.callback(
    Output("cells-dropdown", "options"),
    Input("cells-nav", "id"),
    State("app-store", "data")
)
def initialize(nav, data):
    return [{"label": x, "value": x} for x in data['nci_60_fd']]


@dash.callback(
    Output("cells-content", "children"),
    Input("cells-dropdown", "value"),
    prevent_initial_call=True
)
def create_cell_graphs(cell):
    graphs = dataService.get_cell_graphs(cell)
    card = dbc.Card(id='cell-content-card', children=[
        dbc.CardHeader(html.H3(f'Cell {cell}')),
        dbc.CardBody([
            dcc.Graph(figure=graphs[0]),
            dcc.Graph(figure=graphs[1]),
            dcc.Graph(figure=graphs[2]),
            dcc.Graph(figure=graphs[3]),
            dcc.Graph(figure=graphs[4]),
        ]),

    ])

    return card


layout = dbc.Row(children=[dbc.Col(left_select, width=2, style=ROW_PADDING),
                           dbc.Col(dcc.Loading(id='cells-content-loading', type='default',
                                               children=html.Div(
                                                   children=html.P('Please select NSC'),
                                                   id='cells-content')
                                               ), width=10, style=ROW_PADDING)])
