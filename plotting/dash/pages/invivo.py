import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from .dataservice import dataService

dash.register_page(__name__, path='/invivo')

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}

left_select = dbc.Card(body=True, children=[
    html.Div(id='input-form-div', children=[
        dbc.Form(id='input-form', children=[
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select Experiment Number", html_for="s-expid-dropdown"),
                    dcc.Dropdown(id="s-expid-dropdown", placeholder="Select")
                ])
            ], style=ROW_PADDING),
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select NSC Number", html_for="s-nsc-dropdown"),
                    dcc.Dropdown(id="s-nsc-dropdown", disabled=True)
                ])
            ], style=ROW_PADDING),
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select Group Number", html_for="s-group-dropdown"),
                    dbc.Select(id="s-group-dropdown", disabled=True)
                ])
            ], style=ROW_PADDING)
        ])
    ])
])


@dash.callback(
    Output("s-expid-dropdown", "options"),
    Input("invivo-nav", "id"),
    State("app-store", "data")
)
def initialize(nav, data):
    print('Initialized Invivo Experiment ID dropdown')
    return [{"label": x, "value": x} for x in data['invivo_dict'].keys()]


@dash.callback(
    Output(component_id='s-nsc-dropdown', component_property='options'),
    Output(component_id='s-nsc-dropdown', component_property='disabled'),
    Output(component_id='s-group-dropdown', component_property='options'),
    Output(component_id='s-group-dropdown', component_property='disabled'),
    Input(component_id='s-expid-dropdown', component_property='value'),
    Input(component_id='s-nsc-dropdown', component_property='value'),
    State("app-store", "data"),
    prevent_initial_call=True
)
def handle_selections(expid, nsc, data):
    changed = ctx.triggered_id
    if (changed == 's-expid-dropdown') and (expid is not None):
        nscs = data['invivo_dict'][expid]
        return [{"label": "Control", "value": x} if (x == 999999) else {"label": x, "value": x} for x in
                nscs], False, [], True
    elif (changed == 's-nsc-dropdown') and (expid is not None):
        nscs = data['invivo_dict'][expid]
        group_nbrs = dataService.get_invivo_group_numbers(nsc, expid)
        group_labels = [{"label": "1 - Control", "value": x} if (x == 0) else {"label": x + 1, "value": x} for x in
                        group_nbrs]
        return [{"label": "Control", "value": x} if (x == 999999) else {"label": x, "value": x} for x in
                nscs], False, group_labels, False
    else:
        return ['error'], True, ['error'], True


@dash.callback(
    Output(component_id='s-graph-content', component_property='children'),
    Input(component_id="s-graph-tabs", component_property="active_tab"),
    Input(component_id='s-group-dropdown', component_property='value'),
    State(component_id='s-nsc-dropdown', component_property='value'),
    State(component_id='s-expid-dropdown', component_property='value')
)
def get_graphs(active_tab, group, nsc, expid):
    changed = ctx.triggered_id
    if (group is None) or (not ctx.triggered):
        return html.P('Please select Exp Nbr, NSC, and Group')
    else:
        if active_tab == 'summ-tab':
            data = dataService.get_invivo_summary_plots(expid)
            desc = data['descriptions']
            rows = [
                dbc.Row(dbc.Col(html.H5(f'Summary of Invivo NSC {nsc} | Expid {data["expid"]}'))),
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=data['net_wt_fig']), width=6),
                    dbc.Col(dcc.Graph(figure=data['tum_wt_fig']), width=6)
                ]),
                dbc.Row(dbc.Col(html.P(f'Implant Date: {data["implant_dt"]}, Staging Date: {data["staging_dt"]}'))),
                dbc.Row(
                    dbc.Col(dbc.Table([html.Thead(html.Tr([html.Th('Groups'), html.Th('Description')]))] +
                                      [html.Tbody(
                                          [html.Tr([html.Td(x['group']), html.Td(x['description'])]) for x in desc])
                                       ]
                                      , bordered=True))
                )
            ]
            return rows
        if active_tab == 'survival-tab':
            return dcc.Graph(figure=dataService.get_km_graph(expid, nsc, group))
        if active_tab == 'average-tab':
            figures = dataService.get_anml_weight_graphs(expid, nsc, group)

            # Keys are weight and tumor
            graphs = [
                dbc.Row(dcc.Graph(figure=figures['weight'])),
                dbc.Row(dcc.Graph(figure=figures['tumor']))
            ]
            return graphs
        if active_tab == 'boxes-tab':
            figures = dataService.get_invivo_box_plots(expid, nsc, group)

            graphs = [
                dbc.Row(dcc.Graph(figure=figures['weight'])),
                dbc.Row(dcc.Graph(figure=figures['tumor']))
            ]
            return graphs
        return html.P('Please select Exp Nbr, NSC, and Group')


layout = dbc.Row(children=[
    dbc.Col(left_select, width=2),
    dbc.Col(dbc.Card([
        dbc.CardHeader(
            dbc.Tabs(
                [
                    dbc.Tab(tab_id='summ-tab', label="Summary"),
                    dbc.Tab(tab_id='survival-tab', label="Survival"),
                    dbc.Tab(tab_id='average-tab', label="Averages"),
                    dbc.Tab(tab_id='boxes-tab', label="Boxes")
                ],
                active_tab='summ-tab',
                id='s-graph-tabs',
            )),
        dbc.CardBody(dcc.Loading(id='s-graph-content-loading', type='default',
                                 children=html.Div(html.P('Please select Exp Nbr, NSC, and Group'),
                                                   id='s-graph-content')))
    ]), width=10
    )
], style=ROW_PADDING)
