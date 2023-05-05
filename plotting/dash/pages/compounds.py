import base64
import os
import urllib

import dash
from dash import html, dcc, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, rdDistGeom, rdDepictor
import dash_bootstrap_components as dbc
from rdkit.Chem.Draw import rdMolDraw2D

from .dataservice import dataService
from pathlib import Path

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
                    dbc.Label("Choose one", html_for="co-radio"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Preferred Name", "value": 1},
                            {"label": "NSC No.", "value": 2}
                        ], id='co-radio'),
                    html.Hr(),
                    dcc.Dropdown(id="co-nsc-dropdown"),
                    html.Br(),
                    dbc.Button("Submit", id='co-submit', n_clicks=0)
                ])
            ], style=ROW_PADDING)
        ])
    ])
])

@dash.callback(
    Output("co-nsc-dropdown", "options"),
    Input("co-nsc-dropdown", "search_value"),
    State("co-radio", "value")
)
def initialize(search_value, radio):
    if not search_value:
        raise PreventUpdate
    if radio == 1:
        results = dataService.COMPOUNDS_COLL.aggregate([
            {
                '$match': {
                      '$text': {
                        '$search': search_value
                      }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'nsc': 1,
                    'preferred_name': 1
                }
            }, {
                '$limit': 10
            }
        ])

        # Create options list for the dropdown
        options = [{'label': r['preferred_name'][0], 'value': r['nsc']} for r in results]

        return options
    if radio == 2:
        results = dataService.COMPOUNDS_COLL.aggregate([
            {
                '$match': {
                    'char_nsc': {'$regex': search_value }
                }
            }, {
                '$project': {
                    '_id': 0,
                    'nsc': 1
                }
            }, {
                '$limit': 10
            }
        ])

        # Create options list for the dropdown
        options = [{'label': r['nsc'], 'value': r['nsc']} for r in results]

        return options


@dash.callback(
    Output("co-content", "children"),
    Input("co-submit", "n_clicks"),
    State("co-nsc-dropdown","value"),
    prevent_initial_call=True
)
def get_compound(nclicks, nsc):

    comp = dataService.get_comp_data(nsc)
    smiles = comp['mv_dtp_disregistration_short']['canonicalsmiles']
    mol = Chem.MolFromSmiles(smiles)
    svg = rdMolDraw2D.MolDraw2DSVG(350, 300)
    svg.DrawMolecule(mol)
    svg.FinishDrawing()
    # print(f'SVG TEXT: {svg.GetDrawingText()}')
    data_uri = "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(svg.GetDrawingText())

    # comp_table = get_comp_table(comp)
    # Experiment should have 'Expid' , 'Type' , 'Description'
    df = dataService.get_all_expids_by_nsc(nsc)
    table = dash_table.DataTable(
        df.to_dict('records'),
        id='co-table',
        sort_by=[{'column_id': 'Expid', 'direction': 'asc'}, {'column_id':'Type', 'direction': 'asc'}],
        sort_action="native",
        sort_mode="multi",
        )

    card = dbc.Card(id='co-content-card', children=[
        dbc.CardHeader(html.H4(f'NSC {nsc} | {comp["preferred_name"][0]}')),
        dbc.CardBody([html.Img(src=data_uri), html.Hr(), table])
    ])

    return card


# This builds a HTML table.  It's not quite what we want anymore.
def get_comp_table(comp):
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
