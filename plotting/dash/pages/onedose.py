import dash
from dash import html, dcc, Input,Output,State,ctx
import dash_bootstrap_components as dbc

from .dataservice import DataService

dash.register_page(__name__, path='/onedose')
dataService = DataService()
expids = dataService.ONEDOSE_DICT

ROW_PADDING = {
        "paddingTop":"calc(var(--bs-gutter-x) * .5)",
        "paddingBottom":"calc(var(--bs-gutter-x) * .5)"
    }

left_select = dbc.Card(id='c-sel-card',body=True,children=[
        html.Div(id='od-input-form-div', children=[
            dbc.Form(id='od-input-form', children=[
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment ID", html_for="od-expid-dropdown"),
                        dbc.Select(id="od-expid-dropdown", options=[{"label":x,"value":x} for x in expids])
                    ])
                ],style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select NSC Number", html_for="od-nsc-dropdown"),
                        dbc.Select(id="od-nsc-dropdown")
                    ])
                ],style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid gap-2', children=[
                        dbc.Button("Submit",id="od-submit-button",n_clicks=0, disabled=True)
                    ])
                ])
            ])
        ])
    ])

@dash.callback(
    Output(component_id='od-nsc-dropdown', component_property='options'),
    Output(component_id='od-submit-button', component_property='disabled'),
    Input(component_id='od-expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_nscs(expid):
    nscs = expids[expid]
    return [{"label":x,"value":x} for x in nscs], False

@dash.callback(
    Output(component_id='od-graph-content', component_property='children'),
    Input(component_id='od-submit-button',component_property='n_clicks'),
    Input(component_id="od-graph-tabs", component_property="active_tab"),
    State(component_id='od-nsc-dropdown', component_property='value'),
    State(component_id='od-expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_graphs(conc_clicks,active_tab,nsc,expid):
    changed = ctx.triggered_id
    if (nsc is None) or (not ctx.triggered):
        return html.P('Please select Exp ID and NSC')
    df = dataService.get_od_df_by_nsc(nsc,expid)
    graphs = dataService.get_od_growth_graphs(df,expid,nsc)
    if active_tab == 'od-conc-resp-all':
        return dcc.Graph(figure=graphs[0],style={'height':'700px'})
    if active_tab == 'od-mean-growth':
        return dcc.Graph(figure=graphs[1],style={'height':'700px'})

layout = dbc.Row(children=[
    dbc.Col(left_select, width=2),
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
        dbc.CardBody(html.P('Please select Exp Nbr, NSC'),id='od-graph-content',)
        ]),
        width=10
    )
],style=ROW_PADDING)