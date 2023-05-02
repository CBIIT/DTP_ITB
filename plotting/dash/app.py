# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import json
from dash import Dash, html, dcc, Output, Input
import dash
import dash_bootstrap_components as dbc
from pages.dataservice import dataService

app = Dash(
    __name__,
    use_pages=True,
    title='DCTD Data Plots',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)


# Initialize the shared data and store it in dcc.store
# This is a refactoring adventure to simplify DataService
@app.callback(
    Output('app-store', 'data'),
    Output('initializer', 'children'),
    Input('initializer', 'style')
)
def initialize(_):
    data_dict = {}

    fd_dict = load_exp_ids()
    data_dict['fd_dict'] = fd_dict
    print(f'Five dose exp ids loaded...')

    data_dict['compounds'] = load_comp_nscs()
    print(f'Compound NSCs loaded...')

    data_dict['invivo_dict'] = get_invivo_expids()
    print(f'Invivo Exp Nbrs loaded...')

    data_dict['onedose_dict'] = get_od_expids()
    print(f'One Dose expIds loaded...')

    data_dict['nci_60_fd'] = get_fd_cells()
    return data_dict, html.I('Modules Initialized')

    # Functions to load data


def get_fd_cells():
    return [d['_id'] for d in
            (dataService.CELLS_COLL.aggregate(
                [
                    {
                        '$project': {
                            '_id': 1,
                            'results': 0
                        }
                    }
                ]
            ))
            ]


def load_comp_nscs():
    return [d['nsc'] for d in
            (dataService.COMPOUNDS_COLL.aggregate([
                {
                    '$match': {
                        'soldata': {
                            '$exists': True
                        },
                        'cas': {
                            '$exists': True
                        },
                        'mf': {
                            '$exists': True
                        },
                        'mw': {
                            '$exists': True
                        },
                        'distribution_code_desc': {
                            '$exists': True
                        },
                        'agreement_type_desc': {
                            '$exists': True
                        },
                        'mv_dtp_disregistration_short': {
                            '$exists': True
                        },
                        'cmpd_chem_name': {
                            '$exists': True
                        }
                    }
                }, {
                    '$project': {
                        '_id': 0,
                        'nsc': 1
                    },

                }
            ]))
            ]


def load_exp_ids():
    fd = {}
    data = [fd.update({d['expid']: fd_helper(d['fivedosensc'])}) for d in
            dataService.FIVEDOSE_COLL.aggregate([
                {
                    '$project': {
                        'expid': 1,
                        'fivedosensc': 1,
                        '_id': 0
                    }
                }
            ])
            ]
    return fd


def fd_helper(d):
    return [int(d) for d in d.replace('\'', '').split(',')]


def get_invivo_expids():
    data = dataService.INVIVO_COLL.aggregate([
        {
            '$project': {
                'expid': 1,
                'invivonsc': 1,
                '_id': 0
            }
        }
    ])
    data = [d for d in data]
    invivo_dict = {}
    for invivo in data:
        try:
            nscs = []
            if 'invivonsc' in invivo.keys():
                nscs = invivo['invivonsc'].replace('\'', '').split(',')
                nscs = [int(x) for x in nscs]
            if invivo['expid'] in invivo_dict.keys():
                if len(nscs) > 0:
                    existing_nscs = invivo_dict[invivo['expid']]
                    for x in nscs:
                        if x not in existing_nscs:
                            existing_nscs.append(x)
                    existing_nscs.sort()
                    invivo_dict[invivo['expid']] = existing_nscs
                else:
                    invivo_dict[invivo['expid']] = nscs
            else:
                invivo_dict[invivo['expid']] = nscs
        except KeyError:
            print(f'KEY ERROR invivo_dict: {invivo}')
    return invivo_dict


def get_od_expids():
    data = dataService.ONEDOSE_COLL.aggregate([
        {
            '$project': {
                'expid': 1,
                'onedosensc': 1,
                '_id': 0
            }
        }
    ])
    data = [d for d in data]
    onedose_dict = {}
    for od in data:
        nscs = od['onedosensc'].replace('\'', '').split(',')
        nscs = [int(x) for x in nscs]
        onedose_dict[str(od['expid'])] = nscs
    return onedose_dict


#### NAV STUFF ###########
nav = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Home", active="exact", href="/", id='home-nav')),
        dbc.NavItem(dbc.NavLink("Invivo", active="exact", href="/invivo", id='invivo-nav')),
        dbc.NavItem(dbc.NavLink("Five Dose", active="exact", href="/fivedose", id='fivedose-nav')),
        dbc.NavItem(dbc.NavLink("One Dose", active="exact", href="/onedose", id='onedose-nav')),
        dbc.NavItem(dbc.NavLink("By Cell", active="exact", href="/cells", id='cells-nav')),
        dbc.NavItem(dbc.NavLink("Compounds", active="exact", href="/comps", id='comps-nav'))
    ],
    pills=True,
    navbar=True
)

################################
# ++++++++++++++++ Application Layout +++++++++++++++
app.layout = dbc.Container(
    fluid=True,
    class_name='text-center',
    children=[
        dbc.Row(html.H1('DCTD Graphs and Plots')),
        dbc.Row(dbc.Col(dbc.Navbar(nav), width=12, id='nav-bar-col'), id='nav-bar-row'),
        dbc.Row(dbc.Col(dash.page_container, width=12), id='page-container-col'),
        html.Br(),
        dcc.Loading([
            dcc.Store(id='app-store'),
            html.Div(id='initializer')
        ])
    ]
)
# +++++++++++++++++++++++++++++++++++++++++++++++++++


# ********** Start The server Here **********
if __name__ == '__main__':
    app.run_server(debug=True)
# *******************************************
