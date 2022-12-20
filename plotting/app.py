# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output, State, ctx
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

from dataservice import DataService

app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])

dataService = DataService()
expids = dataService.EXPIDS

ROW_PADDING = {
        "paddingTop":"calc(var(--bs-gutter-y) * .5)",
        "paddingBottom":"calc(var(--bs-gutter-y) * .5)"
    }

################ Left Nav Bar ###############
left_nav = dbc.Col(style=ROW_PADDING, id='left-nav-bar', width=2, children = [dbc.Card(body=True,children=[
        html.Div(id='input-form-div', children=[
            dbc.Form(id='input-form', children=[
                dbc.Row(style=ROW_PADDING, children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment ID", html_for="expid-dropdown"),
                        dbc.Select(id="expid-dropdown", options=[{"label":x,"value":x} for x in        
                            expids])
                    ])
                ]),
                dbc.Row(style=ROW_PADDING, children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select NSC Number", html_for="nsc-dropdown"),
                        dbc.Select(id="nsc-dropdown")
                    ])
                ]),
                dbc.Row(style=ROW_PADDING, children=[
                    html.Div(className='d-grid gap-2', children=[
                        dbc.Button("Conc Response",id="conc-resp-button",n_clicks=0, disabled=True)
                    ])
                ]),
                
                dbc.Row(style=ROW_PADDING, children=[
                    html.Div(className='d-grid gap-2', children=[
                        dbc.Button("Mean Graph",id="mean-graph-button",n_clicks=0, disabled=True)
                    ])
                ])
            ])
        ])
    ])
])
############################################

# ********** Application Layout **********
app.layout = dbc.Container(fluid=True, class_name='text-center', children=[
    html.H1('NCI-60 Graphs and Plots'),
    dbc.Row(children=[
        left_nav,
        dbc.Col(id='graph-container', width=10)
    ])
])
# *******************************************



# ********** Call Back Functions **********
@app.callback(
    Output(component_id='nsc-dropdown', component_property='options'),
    Output(component_id='conc-resp-button', component_property='disabled'),
    Output(component_id='mean-graph-button', component_property='disabled'),
    Input(component_id='expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def handle_dropdowns(expid):
    nscs = dataService.NSC_DICT[expid]
    return [{"label":x,"value":x} for x in nscs], False, False

@app.callback(
    Output(component_id='graph-container', component_property='children'),
    Input(component_id='conc-resp-button',component_property='n_clicks'),
    Input(component_id='mean-graph-button',component_property='n_clicks'),
    State(component_id='nsc-dropdown', component_property='value'),
    State(component_id='expid-dropdown', component_property='value'),
    prevent_initial_call=True
)
def get_graphs(conc_clicks,mean_clicks,nsc,expid):
    button_id = ctx.triggered_id
    #TODO: distinguish between which button was clicked and then process the data

    df = dataService.get_df_by_nsc(nsc,expid)
    data_dict = dataService.create_grouped_data_dict(df)
    panel_graphs = []
    for panel in data_dict.keys():
        panel_graph = dataService.get_conc_resp_graph_by_panel(
            data_dict[panel],nsc,panel
            )
        panel_graphs.append(dbc.Card(body=True,children =[dcc.Graph(id=f'{panel}-graph', figure=panel_graph)]))
    # Create a 3 x 3 layout
    
    rows = [dbc.Row(id=f'graphs-row-{x}',children=[], style=ROW_PADDING) for x in range(0,3)]
    for idx,graph in enumerate(panel_graphs):
        if idx > 2 and idx < 6:
            rows[1].children.append(dbc.Col(id=f'graphs-{idx}',children=[graph],width=4))
        elif idx > 5:
            rows[2].children.append(dbc.Col(id=f'graphs-{idx}',children=[graph],width=4))
        else:
            rows[0].children.append(dbc.Col(id=f'graphs-{idx}',children=[graph],width=4))
    return *rows, False, True # Conc_resp_graphs, Graph Container=False, meanGraphContainer=True

#@app.callback(
#    Output(component_id='mean-graph-container', component_property='children'),
##    Output(component_id='mean-graph-container', component_property='hidden'),
 #   Output(component_id='graph-container', component_property='hidden'),
#    Input(component_id='mean-graph-button', component_property='n_clicks'),
#    State(component_id='nsc-dropdown', component_property='value'),
#    State(component_id='expid-dropdown', component_property='value'),
#    prevent_initial_call=True
#)
#def get_mean_graph(n_clicks,nsc,expid):
 #   return [html.P('TO BE BUILT!')], True, False

# ****************************************




# ********** Start The server Here **********
if __name__ == '__main__':
    app.run_server(debug=True)
# *******************************************