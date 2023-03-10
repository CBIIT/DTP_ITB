import dash
from dash import html
import dash_bootstrap_components as dbc

ROW_PADDING = {
        "paddingTop":"calc(var(--bs-gutter-x) * .5)",
        "paddingBottom":"calc(var(--bs-gutter-x) * .5)"
    }

################ select Bar ###############
left_select = dbc.Card(body=True,children=[
        html.Div(id='input-form-div', children=[
            dbc.Form(id='input-form', children=[
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment ID", html_for="expid-dropdown"),
                        dbc.Select(id="expid-dropdown", options=[{"label":x,"value":x} for x in dataService.EXPIDS])
                    ])
                ],style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select NSC Number", html_for="nsc-dropdown"),
                        dbc.Select(id="nsc-dropdown")
                    ])
                ],style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid gap-2', children=[
                        dbc.Button("Submit",id="submit-button",n_clicks=0, disabled=True)
                    ])
                ])
            ])
        ])
    ])
############################################

def sidebar():
    return left_select