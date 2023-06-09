"""
One Dose
This page represents the content necessary to render all things for the One Dose section.

"""
import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc

from .dataservice import dataService

# The page is registered with the main application along with a static root route and a dynamic route
# for when the user clicks on a one dose experiment from the compounds page.
dash.register_page(__name__, path='/onedose', path_template='/onedose/<expid>/<nsc>')

# Variable for CSS spacing
ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}


def get_left_select(nsc, expid):
    """
    Renders the Left side dropdown menus and handles when routed to the page by compounds list link.
    :param nsc: nsc specified from compounds list
    :param expid: expid specified from the compounds list
    :return: Card: dash bootstrap component Card of the dropdown menus
    """
    if nsc is None and expid is None:
        expid_dropdown = dcc.Dropdown(id="od-expid-dropdown")
        nsc_dropdown = dcc.Dropdown(id="od-nsc-dropdown")
    else:
        expid_dropdown = dcc.Dropdown(id="od-expid-dropdown", value=expid,
                                      options=[{'label': expid, 'value': expid}])
        nsc_dropdown = dcc.Dropdown(id="od-nsc-dropdown", value=nsc, options=[{'label': nsc, 'value': nsc}])

    return dbc.Card(id='c-sel-card', body=True, children=[
        html.Div(id='od-input-form-div', children=[
            dbc.Form(id='od-input-form', children=[
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment ID", html_for="od-expid-dropdown"),
                        expid_dropdown
                    ])
                ], style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select NSC Number", html_for="od-nsc-dropdown"),
                        nsc_dropdown
                    ])
                ], style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid gap-2', children=[
                        dbc.Button("Submit", id="od-submit-button", n_clicks=0, disabled=True)
                    ])
                ])
            ])
        ])
    ])


@dash.callback(
    Output("od-expid-dropdown", "options"),
    Input("onedose-nav", "id"),
    State("app-store", "data")
)
def initialize(nav, data):
    """
    Provides the 25 pre-loaded experiment IDs from the dcc.Store object.
    :param nav: dummy object used to help hook
    :param data: dcc.Store component that contains application data loaded in app.py
    :return: list: the list of labels and values stored in the onedose_dict of 25 or less
                    in the left menu dropdown selections.
    """
    return [{"label": x, "value": x} for x in data['onedose_dict'].keys()]


@dash.callback(
    Output(component_id='od-nsc-dropdown', component_property='options'),
    Output(component_id='od-nsc-dropdown', component_property='value'),
    Output(component_id='od-submit-button', component_property='disabled'),
    Input(component_id='od-expid-dropdown', component_property='value'),
    State("app-store", "data"),
    prevent_initial_call=True
)
def get_nscs(expid, data):
    """
    Retrieves associated NSCs with the provided experiment ID.
    :param expid: onedose experiment ID
    :param data: dcc.Store accessor object
    :return: list: list of NSCs in the experiment
            string: displayed value of populated dropdown for user experience
            boolean: enable or disable the button to submit for data
    """
    nscs = data['onedose_dict'][expid]
    if len(nscs) > 0:
        return [{"label": x, "value": x} for x in nscs], nscs[0], False
    else:
        return [], 'None Found', True


@dash.callback(
    Output(component_id='od-graph-content', component_property='children'),
    Input(component_id='od-submit-button', component_property='n_clicks'),
    Input(component_id="od-graph-tabs", component_property="active_tab"),
    State(component_id='od-nsc-dropdown', component_property='value'),
    State(component_id='od-expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_graphs(conc_clicks, active_tab, nsc, expid):
    """
    Creates and communicates with backend services to generate graphs depending on the tab currently open.
    :param conc_clicks: used to hook button click event to this function
    :param active_tab: the value of the tab that is currently marked active
    :param nsc: NSC for which data will be retrieved with respect to the experiment
    :param expid: Experiment ID for which data will be sourced
    :return: dcc.Graph: The Plotly graph wrapper in which the graph figure is contained.
    """

    # Default load displays a message to user to select from the dropdowns
    if (nsc is None) or (not ctx.triggered):
        return html.P('Please select Exp ID and NSC')

    # Retrieve a dataFrame representation of the One dose data that will be used for making the graph
    df = dataService.get_od_df_by_nsc(nsc, expid)

    # Creates a list of Plotly plots for one dose data through the data service to display depending on
    # which tab (type of graph) is selected.
    graphs = dataService.get_od_growth_graphs(df, expid, nsc)
    if active_tab == 'od-conc-resp-all':
        return dcc.Graph(figure=graphs[0], style={'height': '700px'})
    if active_tab == 'od-mean-growth':
        return dcc.Graph(figure=graphs[1], style={'height': '700px'})


def layout(nsc=None, expid=None):
    """
    The Root container for the layout of the One Dose content page. This can handle extracting the parameters from the
    URL.
    :param nsc: If routed through compounds list link, this is the NSC from there
    :param expid: If routed through the compounds list link, this is the Experiment ID from there
    :return: dbc.Row: the dash bootstrap components Row container that has all the components of the page.
    """
    if nsc is None and expid is None:
        body = dbc.CardBody(dcc.Loading(id='od-graph-content-loading', type='default',
                                        children=html.Div(html.P('Please select Exp Nbr, NSC'),
                                                          id='od-graph-content', )))
    else:
        body = dbc.CardBody(
                    dcc.Loading(
                        id='od-graph-content-loading',
                        type='default',
                        children=html.Div(
                                id='od-graph-content',
                                children=get_graphs(0, 'od-conc-resp-all', nsc, expid)
                            )
                        )
                    )

    return dbc.Row(children=[
        dbc.Col(get_left_select(nsc, expid), width=2),
        dbc.Col(dbc.Card([
            dbc.CardHeader(
                dbc.Tabs(
                    [
                        dbc.Tab(tab_id='od-conc-resp-all', label="Average Growth"),
                        dbc.Tab(tab_id='od-mean-growth', label="Average Mean Growth"),
                    ],
                    active_tab='od-conc-resp-all',
                    id='od-graph-tabs',
                )),
            dbc.CardBody(dcc.Loading(id='od-graph-content-loading', type='default',
                                     children=html.Div(html.P('Please select Exp Nbr, NSC'), id='od-graph-content', )))
        ]),
            width=10
        )
    ], style=ROW_PADDING)
