import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from .dataservice import dataService

dash.register_page(__name__, path='/fivedose', path_template='/fivedose/<expid>/<nsc>')
# expids = dataService.EXPIDS

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}


def get_left_select(expid, nsc):
    if expid is None and nsc is None:
        expid_dropdown = dcc.Dropdown(id="expid-dropdown")
        nsc_dropdown = dcc.Dropdown(id="nsc-dropdown")
    else:
        expid_dropdown = dcc.Dropdown(id="expid-dropdown", value=expid, options=[{'label': expid, 'value': expid}])
        nsc_dropdown = dcc.Dropdown(id="nsc-dropdown", value=nsc, options=[{'label': nsc, 'value': nsc}])

    return dbc.Card(id='c-sel-card', body=True, children=[
        html.Div(id='c-input-form-div', children=[
            dbc.Form(id='c-input-form', children=[
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment ID", html_for="expid-dropdown"),
                        expid_dropdown
                    ])], style=ROW_PADDING),
                dbc.Row(dbc.Button("Get NSCs", id='c-get-nscs', n_clicks=0), style=ROW_PADDING),
                html.Hr(),

                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select NSC Number", html_for="nsc-dropdown"),
                        nsc_dropdown
                    ])
                ], style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid gap-2', children=[
                        dbc.Button("Submit", id="submit-button", n_clicks=0, disabled=True)
                    ])
                ])
            ])
        ])
    ])


@dash.callback(
    Output("expid-dropdown", "options"),
    Input('expid-dropdown', 'search_value'),
    State("app-store", "data"),
    prevent_initial_call=True
)
def initialize(search_value, data):
    if not search_value:
        return [{"label": x, "value": x} for x in data['fd_dict'].keys()]
    else:
        results = dataService.FIVEDOSE_COLL.aggregate([
            {
                '$match': {
                    'expid': {'$regex': str(search_value)}
                }
            }, {
                '$project': {
                    '_id': 0,
                    'expid': 1
                }
            }, {
                '$limit': 10
            }
        ])
        options = [{'label': r['expid'], 'value': r['expid']} for r in results]

        return options


@dash.callback(
    Output(component_id='nsc-dropdown', component_property='options', allow_duplicate=True),
    Output(component_id='nsc-dropdown', component_property='value'),
    Output(component_id='submit-button', component_property='disabled'),
    Input("c-get-nscs", "n_clicks"),
    State(component_id='expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_nscs(n_clicks, expid):
    nscs = dataService.get_nscs_by_expid(expid)
    if len(nscs) > 0:
        return [{"label": x, "value": x} for x in nscs], nscs[0], False
    else:
        return [], 'None Found', True


@dash.callback(
    Output(component_id='graph-content', component_property='children', allow_duplicate=True),
    Input(component_id='submit-button', component_property='n_clicks'),
    Input(component_id="graph-tabs", component_property="active_tab"),
    State(component_id='nsc-dropdown', component_property='value'),
    State(component_id='expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_graphs(conc_clicks, active_tab, nsc, expid):
    if (nsc is None) or (not ctx.triggered):
        return html.P('Please select Exp Nbr, NSC, and Group')
    df = dataService.get_df_by_nsc(nsc, expid)

    if active_tab == 'conc-resp-all':
        return dcc.Graph(figure=dataService.get_conc_resp_graph(df, nsc), style={'height': '700px'})
    if active_tab == 'conc-resp':
        data_dict = dataService.create_grouped_data_dict(df)
        panel_graphs = []
        for panel in data_dict.keys():
            panel_graph = dataService.get_conc_resp_graph_by_panel(
                data_dict[panel], nsc, panel
            )
            panel_graphs.append(dbc.Card(body=True, children=[dcc.Graph(id=f'{panel}-graph', figure=panel_graph)]))
        # Create a 3 x 3 layout
        # There is a better way, but my head was tired at this point.
        rows = [dbc.Row(id=f'graphs-row-{x}', children=[], style=ROW_PADDING) for x in range(0, 3)]
        for idx, graph in enumerate(panel_graphs):
            if idx > 2 and idx < 6:
                rows[1].children.append(dbc.Col(id=f'graphs-{idx}', children=[graph], width=4))
            elif idx > 5:
                rows[2].children.append(dbc.Col(id=f'graphs-{idx}', children=[graph], width=4))
            else:
                rows[0].children.append(dbc.Col(id=f'graphs-{idx}', children=[graph], width=4))
        return rows  # Conc_resp_graphs, Graph Container=False, meanGraphContainer=True

    if active_tab == 'gi-50':
        print(f'IN GI-50: {active_tab}')
        dataService.get_mean_graphs_data(nsc, expid)
        return dcc.Graph(figure=dataService.get_gi50_graph(nsc))
    if active_tab == 'lc-50':
        dataService.get_mean_graphs_data(nsc, expid)
        return dcc.Graph(figure=dataService.get_lc50_graph(nsc))
    if active_tab == 'tgi':
        dataService.get_mean_graphs_data(nsc, expid)
        return dcc.Graph(figure=dataService.get_tgi_graph(nsc))
    if active_tab == 'heatmap':
        return dbc.Col([
            dbc.Row([
                dbc.Label("Choose Type"),
                dbc.Select(
                    id="conc-heat-type",
                    options=[
                        {"label": "GI50", "value": "gi50"},
                        {"label": "LC50", "value": "lc50"},
                        {"label": "TGI", "value": "tgi"}
                    ])
                ]
            ),
            dbc.Row(id='conc-heat-map-content')
        ])

@dash.callback(
    Output(component_id='conc-heat-map-content', component_property='children'),
    Input(component_id='conc-heat-type', component_property='value'),
    State(component_id='expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def load_heatmaps(heatmap_type, expid):
    return dcc.Loading(dcc.Graph(figure=dataService.get_fivedose_heatmap(expid, heatmap_type)))


def layout(expid=None, nsc=None):
    if expid is None or nsc is None:
        card_body = dcc.Loading(id='graph-content-loading', type='default',
                                children=html.Div(html.P('Please select Exp Nbr, NSC'), id='graph-content'))
    else:
        card_body = dcc.Loading(id='graph-content-loading', type='default',
                                children=html.Div(get_graphs(0, 'conc-resp-all', nsc, expid), id='graph-content'))

    return dbc.Row(children=[
        dbc.Col(get_left_select(expid, nsc), width=2),
        dbc.Col(dbc.Card([
            dbc.CardHeader(
                dbc.Tabs(
                    [
                        dbc.Tab(tab_id='conc-resp-all', label="Conc Response"),
                        dbc.Tab(tab_id='conc-resp', label="Conc Response (Panel)"),
                        dbc.Tab(tab_id='gi-50', label="GI50"),
                        dbc.Tab(tab_id='tgi', label="TGI"),
                        dbc.Tab(tab_id='lc-50', label="LC50"),
                        dbc.Tab(tab_id='heatmap', label="Exp Heatmap")
                    ],
                    active_tab='conc-resp-all',
                    id='graph-tabs',
                )),
            dbc.CardBody(
                card_body
            )
        ]),
            width=10
        )
    ], style=ROW_PADDING)
