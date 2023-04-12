import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from .dataservice import dataService

dash.register_page(__name__, path='/comps')

#nscs = dataService.COMP_NSCS

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}

left_select = dbc.Card(id='co-sel-card', body=True, children=[
    html.Div(id='co-input-form-div', children=[
        dbc.Form(id='co-input-form', children=[
            dbc.Row(children=[
                html.Div(className='d-grid', children=[
                    dbc.Label("Select NSC", html_for="co-nsc-dropdown"),
                    dcc.Dropdown(id="co-nsc-dropdown")
                ])
            ], style=ROW_PADDING)
        ])
    ])
])

@dash.callback(
    Output("co-nsc-dropdown","options"),
    Input("comps-nav","id"),
    State("app-store","data")
)
def initialize(nav,data):
    return [{"label": x, "value": x} for x in data['compounds']]

@dash.callback(
    Output("co-content", "children"),
    Input("co-nsc-dropdown", "value"),
    prevent_initial_call=True
)
def get_compound(nsc):
    print(f'IN COMPOUNDS LINE 36')
    comp = dataService.get_comp_data(nsc)
    comp_table = get_comp_table(comp)
    card = dbc.Card(id='co-content-card', children=[
        dbc.CardHeader(html.H4(f'NSC {nsc} | {comp["preferred_name"][0]}')),
        dbc.CardImg(src=comp['structure_picture']['simage']),
        dbc.CardBody(comp_table)
    ])

    return card


def get_comp_table(comp):
    print(f'IN COMPOUNDS LINE 49')
    soldata = [(f'Vehicle: {x["vehicle_desc"]}\n' + f'Description: {x["solind_desc"]}\n') for x in comp['soldata']]
    #mat_class_data = [(
          #  f'Classification ID: {x["mat_class_id"]}\n' + f'Status: {x["mc_status_desc"]}\n' + f'Type: {comp["mc_type_desc"]}\n' + f'Code: {comp["mc_code_desc"]}\n')
       # for x in comp['material_classification']]
    #rel_nsc = [(f'NSC: {x["related_nsc"]}\n' + f'How: {x["how_related"]}\n') for x in comp['related_prefix_nsc']]
    chem_names = [(f'Name: {x["name"]}\n' + f'Type: {x["name_type"]}\n') for x in comp['cmpd_chem_name']]
    print(f'IN COMPOUNDS LINE 56')
    table_header = [
        html.Thead(html.Tr([html.Th("Data Field"), html.Th("Value")]))
    ]


    # APPARENTLY COMPOUNDS ARE MISSING A LOT OF THESE FIELDS SO YOU GET KEY ERRORS EVERYWHERE
    row1 = html.Tr([html.Td("CAS"), html.Td(f"{comp['cas']}")])
    row2 = html.Tr([html.Td("MF"), html.Td(f"{comp['mf']}")])
    row3 = html.Tr([html.Td("MW"), html.Td(f"{comp['mw']}")])
    row4 = html.Tr([html.Td("Distribution"), html.Td(f"{comp['distribution_code_desc']}")])
    row5 = html.Tr([html.Td("Agreement Type"), html.Td(f"{comp['agreement_type_desc']}")])
    row6 = html.Tr([html.Td("Can. Smiles"), html.Td(f"{comp['mv_dtp_disregistration_short']['canonicalsmiles']}")])
    row7 = html.Tr([html.Td("Solubility Data"), html.Td(soldata)])
    # row8 = html.Tr([html.Td("Material Classification Data"), html.Td(mat_class_data)])
    # row9 = html.Tr([html.Td("Related NSCs"), html.Td(rel_nsc)])
    row10 = html.Tr([html.Td("Chemical Names"), html.Td(chem_names)])

    table_body = [html.Tbody([row1, row2, row3, row4, row5, row6, row7, row10])]

    table = dbc.Table(table_header + table_body, bordered=True)
    return table


layout = dbc.Row(children=[dbc.Col(left_select, width=2,style=ROW_PADDING),
                           dbc.Col(dcc.Loading(id='co-content-loading', type='default',
                                               children=html.Div(
                                                   children=html.P('Please select NSC'),
                                                   id='co-content')
                                               ), width=10, style=ROW_PADDING)])
