import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import dash_bio as dashbio
from dash.exceptions import PreventUpdate

from .dataservice import dataService

# The page is registered with the main application along with a static root route and a dynamic route
# for when the user clicks on a one dose experiment from the compounds page.
dash.register_page(__name__, path='/oncokb')

# Variable for CSS spacing
ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}


def get_left_select():
    """
    Renders the Left side radio buttons and corresponding dropdowns
    :param
    :return: Card: dash bootstrap component Card of the dropdown menus
    """

    return dbc.Card(id='okb-sel-card', body=True, children=[
        dbc.Form(id='okb-input-form', children=[
            dbc.Row(children=[
                html.Div(id="okb-radio-div", className='d-grid', children=[
                    dbc.Label("Choose one", html_for="okb-radio"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Full - Filtered", "value": 1},
                            {"label": "Full - Unfiltered", "value": 2},
                            {"label": "Cell Line", "value": 3},
                            {"label": "Gene", "value": 4}
                        ], id='okb-radio'),
                ]),
            ]),
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select Criteria", html_for="okb-dropdown"),
                    dcc.Dropdown(id="okb-dropdown", disabled=True)
                ])
            ], style=ROW_PADDING),
            dbc.Row(
                dbc.Button("Submit", id='okb-submit', n_clicks=0, disabled=True)
            )
        ])
    ])


@dash.callback(
    Output("okb-dropdown", "disabled"),
    Output("okb-submit", "disabled"),
    Input("okb-radio", "value"),
    prevent_initial_call=True
)
def enable_dropdown(radio):
    if radio == 3 or radio == 4:
        return False, False
    elif radio == 1 or radio == 2:
        return True, False


@dash.callback(
    Output("okb-dropdown", "options"),
    Input("okb-dropdown", "disabled"),
    State("okb-radio", "value"),
    prevent_initial_call=True
)
def handle_autocomplete_search(disabled, radio):
    if disabled is None:
        raise PreventUpdate
    if radio == 1 or radio == 2:
        # This shouldn't be possible.
        return [{"label": "", "value": ""}]
    elif radio == 3:
        return [{"label": x['cellname'], "value": x['cellname']} for x in dataService.get_onco_cells()]
    elif radio == 4:
        return [{"label": x['gene'], "value": x['gene']} for x in dataService.get_onco_genes()]
    else:
        # This shouldn't be encountered
        return []


@dash.callback(
    Output("okb-content", "children"),
    Input("okb-submit", "n_clicks"),
    State("okb-radio", "value"),
    State("okb-dropdown", "value"),
    prevent_initial_call=True
)
def handle_submit(n_clicks, radio, search):
    # Filtered all
    if radio == 1:
        data = dataService.get_oncoprint_data_filtered().to_dict(orient='records')
        return dcc.Loading(dashbio.OncoPrint(
            id='okb-oncoprint',
            data=data,
            height=1500
        ))
    # Unfiltered all
    elif radio == 2:
        data = dataService.get_oncoprint_data_unfiltered().to_dict(orient='records')
        return dcc.Loading(dashbio.OncoPrint(
            id='okb-oncoprint',
            data=data,
            height=1500
        ))
    # By Cell Line
    elif radio == 3:
        data = dataService.get_onco_by_cell(search).to_dict(orient='records')
        return dcc.Loading(dashbio.OncoPrint(
            id='okb-oncoprint',
            data=data,
            width=600,
            height=1000
        ))
    # By Gene
    elif radio == 4:
        data = dataService.get_onco_by_gene_df(search).to_dict(orient='records')
        return dcc.Loading(dashbio.OncoPrint(
            id='okb-oncoprint',
            data=data,
            height=1000
        ))
    else:
        return html.P("Please make a selection")


def layout():
    return dbc.Row(children=[
        dbc.Col(get_left_select(), width=2, style=ROW_PADDING),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(id='okb-content', style=ROW_PADDING)
            ), style=ROW_PADDING
        )
    ])
