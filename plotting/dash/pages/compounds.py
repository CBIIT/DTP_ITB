"""
The compounds section of the application will allow a user to find a compound and all the associated experiments that
it has been used in. Additionally, there is functionality to draw the compound from the SMILES code that it has.
The list of experiments contains some high-level metadata about the experiment and a link to see plots from the
experiment.
"""
import urllib

import dash
from dash import html, dcc, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, rdDistGeom, rdDepictor
import dash_bootstrap_components as dbc
from rdkit.Chem.Draw import rdMolDraw2D


from .dataservice import dataService

# The page is associated with the main application by this manner
dash.register_page(__name__, path='/comps')

# CSS padding for element spacing
ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}

# The search and dropdown for finding a compound by NSC or preferred name
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
                    dcc.Dropdown(id="co-nsc-dropdown", disabled=True),
                    html.Br(),
                    dbc.Button("Submit", id='co-submit', n_clicks=0)
                ])
            ], style=ROW_PADDING)
        ])
    ])
])

@dash.callback(
    Output("co-nsc-dropdown", "disabled"),
    Input("co-radio", "value")
)
def enable_dropdown(radio):
    if radio == 1 or radio == 2:
        return False
    else:
        return True

@dash.callback(
    Output("co-nsc-dropdown", "options"),
    Input("co-nsc-dropdown", "search_value"),
    State("co-radio", "value")
)
def initialize(search_value, radio):
    """
    This helps with the autocomplete functionality of this section. The first 10 closest results are returned with every
    keystroke.
    :param search_value: string: value entered into the search dropdown input
    :param radio: int: the value that represents whether it is searcing NSC or preferred name.
    :return: list: the label and value key/value pair that are nearest to users search value input.
    """
    if not search_value:
        raise PreventUpdate

    # If the value is 1, it will search on preferred name's text index
    if radio == 1:
        results = dataService.COMPOUNDS_COLL.aggregate([
            {
                '$match': {
                    '$text': {
                        '$search': search_value
                    },
                    'mv_dtp_disregistration_short.canonicalsmiles': {
                        '$exists': True
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

    # If the value is 2 it will search on the NSC's char_nsc field with regex
    if radio == 2:
        results = dataService.COMPOUNDS_COLL.aggregate([
            {
                '$match': {
                    'char_nsc': {'$regex': search_value},
                    'mv_dtp_disregistration_short.canonicalsmiles': {
                        '$exists': True
                    }
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
    State("co-nsc-dropdown", "value"),
    prevent_initial_call=True
)
def get_compound(nclicks, nsc):
    """
    Once the compound has been retrieved, the function renders a SMILES image, metadata, and a list of all the various
    experiments in which it was used.
    :param nclicks: value used to bind the submit button event
    :param nsc: the compound's NSC number
    :return: dbc.Card: wrapper containing a title, SMILES image, searchable table with experiments listed.
    """
    comp = dataService.get_comp_data(nsc)

    # The SMILES 2d image is generated with rdkit, and provides the textual encoding of the image, which the browser
    # can render.
    smiles = comp['mv_dtp_disregistration_short']['canonicalsmiles']
    mol = Chem.MolFromSmiles(smiles)
    svg = rdMolDraw2D.MolDraw2DSVG(350, 300)
    svg.DrawMolecule(mol)
    svg.FinishDrawing()
    data_uri = "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(svg.GetDrawingText())


    # Experiment should have 'Expid' , 'Type' , 'Description'
    df = dataService.get_all_expids_by_nsc(nsc)
    if df.empty:
        card = dbc.Card(id='co-content-card', children=[
            dbc.CardHeader(html.H4(f'NSC {nsc} | {comp["preferred_name"][0]}')),
            dbc.CardBody([html.Img(src=data_uri), html.Hr(), html.P('NSC not found in any experiments.')])
        ])
    else:
        df['Expid'] = df.apply(lambda row: create_links(row['Expid'], row['Type'], nsc), axis=1)

        # Dash data table is a component that accepts a dataframe broken into a dictionary in the records style format.
        # From there it can create all the columnar data
        # columns is a list of the column names in the table
        # id is a standard way to set a unique identifier for the parent table element
        # sort_action enables the native mode for sorting by column values
        # sort_mode is set to multi in order to allow sorting along multiple column values
        # filter action is set to allow the native algorithm of filtering to be enabled
        # markdown_options is set to allow for html-styled strings be rendered
        table = dash_table.DataTable(
            df.to_dict('records'),
            columns=[{'id': x, 'name': x, 'presentation': 'markdown'} if x == 'Expid' else {'id': x, 'name': x} for x in
                     df.columns],
            id='co-table',
            sort_action="native",
            sort_mode="multi",
            filter_action="native",
            markdown_options={"html": True}
        )

        # The card represents the parent container of the body section, and contains the data related to the compound
        card = dbc.Card(id='co-content-card', children=[
            dbc.CardHeader(html.H4(f'NSC {nsc} | {comp["preferred_name"][0]}')),
            dbc.CardBody([html.Img(src=data_uri), html.Hr(), table])
        ])

    return card


def create_links(expid, type, nsc):
    if type == 'One Dose':
        return f'<a href="/onedose/{expid}/{nsc}">{expid}</a>'
    elif type == 'Five Dose':
        return f'<a href="/fivedose/{expid}/{nsc}">{expid}</a>'
    elif type == 'Invivo':
        return f'<a href="/invivo/{expid}/{nsc}">{expid}</a>'
    else:
        raise Exception('Error making link')


# This builds a HTML table.  It's not quite what we want anymore.
# This is a much less dynamic table example that I have decided to ignore for various reasons.
def get_comp_table(comp):
    soldata = [(f'Vehicle: {x["vehicle_desc"]}\n' + f'Description: {x["solind_desc"]}\n') for x in comp['soldata']]
    # mat_class_data = [(
    #  f'Classification ID: {x["mat_class_id"]}\n' + f'Status: {x["mc_status_desc"]}\n' + f'Type: {comp["mc_type_desc"]}\n' + f'Code: {comp["mc_code_desc"]}\n')
    # for x in comp['material_classification']]
    # rel_nsc = [(f'NSC: {x["related_nsc"]}\n' + f'How: {x["how_related"]}\n') for x in comp['related_prefix_nsc']]
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

# The layout variable represents the root container for the compounds page in which
# all the components are contained.
layout = dbc.Row(children=[dbc.Col(left_select, width=2, style=ROW_PADDING),
                           dbc.Col(dcc.Loading(id='co-content-loading', type='default',
                                               children=html.Div(
                                                   children=html.P('Please select NSC'),
                                                   id='co-content')
                                               ), width=10, style=ROW_PADDING)])
