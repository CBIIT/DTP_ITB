import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc

from .dataservice import dataService

dash.register_page(__name__, path='/onedose', path_template='/fivedose/<expid>/<nsc>')
# expids = dataService.ONEDOSE_DICT

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}


def get_left_select(nsc, expid):
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
    changed = ctx.triggered_id
    if (nsc is None) or (not ctx.triggered):
        return html.P('Please select Exp ID and NSC')
    df = dataService.get_od_df_by_nsc(nsc, expid)
    graphs = dataService.get_od_growth_graphs(df, expid, nsc)
    if active_tab == 'od-conc-resp-all':
        return dcc.Graph(figure=graphs[0], style={'height': '700px'})
    if active_tab == 'od-mean-growth':
        return dcc.Graph(figure=graphs[1], style={'height': '700px'})


def layout(nsc=None, expid=None):
    tab = None
    if nsc is None and expid is None:
        tab = dbc.Tab(tab_id='od-conc-resp-all', label="Average Growth")
    else:
        tab = dbc.Tab(tab_id='od-conc-resp-all', label="Average Growth",
                      children=get_graphs(0, 'od-conc-resp-all', nsc, expid))

    return dbc.Row(children=[
        dbc.Col(get_left_select(nsc, expid), width=2),
        dbc.Col(dbc.Card([
            dbc.CardHeader(
                dbc.Tabs(
                    [
                        tab,
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
