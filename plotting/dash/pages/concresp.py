import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc

from .dataservice import dataService

dash.register_page(__name__, path='/fivedose')
# expids = dataService.EXPIDS

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}

left_select = dbc.Card(id='c-sel-card', body=True, children=[
    html.Div(id='c-input-form-div', children=[
        dbc.Form(id='c-input-form', children=[
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select Experiment ID", html_for="expid-dropdown"),
                    dcc.Dropdown(id="expid-dropdown")
                ])
            ], style=ROW_PADDING),
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select NSC Number", html_for="nsc-dropdown"),
                    dcc.Dropdown(id="nsc-dropdown")
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
    Input("fivedose-nav", "id"),
    State("app-store", "data")
)
def initialize(nav, data):
    return [{"label": x, "value": x} for x in data['fd_dict'].keys()]


@dash.callback(
    Output(component_id='nsc-dropdown', component_property='options'),
    Output(component_id='nsc-dropdown', component_property='value'),
    Output(component_id='submit-button', component_property='disabled'),
    Input(component_id='expid-dropdown', component_property='value'),
    State("app-store", "data"),
    prevent_initial_call=True
)
def get_nscs(expid, data):
    nscs = data['fd_dict'][expid]
    if len(nscs) > 0:
        return [{"label": x, "value": x} for x in nscs], nscs[0], False
    else:
        return [], 'None Found', True


@dash.callback(
    Output(component_id='graph-content', component_property='children'),
    Input(component_id='submit-button', component_property='n_clicks'),
    Input(component_id="graph-tabs", component_property="active_tab"),
    State(component_id='nsc-dropdown', component_property='value'),
    State(component_id='expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_graphs(conc_clicks, active_tab, nsc, expid):
    changed = ctx.triggered_id
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


layout = dbc.Row(children=[
    dbc.Col(left_select, width=2),
    dbc.Col(dbc.Card([
        dbc.CardHeader(
            dbc.Tabs(
                [
                    dbc.Tab(tab_id='conc-resp-all', label="Conc Response"),
                    dbc.Tab(tab_id='conc-resp', label="Conc Response (Panel)"),
                    dbc.Tab(tab_id='gi-50', label="GI50"),
                    dbc.Tab(tab_id='tgi', label="TGI"),
                    dbc.Tab(tab_id='lc-50', label="LC50")
                ],
                active_tab='conc-resp-all',
                id='graph-tabs',
            )),
        dbc.CardBody(
            dcc.Loading(id='graph-content-loading', type='default',
                        children=html.Div(html.P('Please select Exp Nbr, NSC'), id='graph-content', ))
        )
    ]),
        width=10
    )
], style=ROW_PADDING)
