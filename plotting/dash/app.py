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
    Input('initializer', 'style')
)
def initialize(_):
    data_dict = {}

    uniques, nsc_dict = load_exp_ids()
    data_dict['fivedose_nscs'] = uniques
    data_dict['nsc_dict'] = nsc_dict
    print(f'Five dose exp ids loaded...')

    data_dict['compounds'] = load_comp_nscs()
    print(f'Compound NSCs loaded...')

    data_dict['invivo_dict'] = get_invivo_expids()
    print(f'Invivo Exp Nbrs loaded...')

    data_dict['onedose_dict'] = get_od_expids()
    print(f'One Dose expIds loaded...')
    return data_dict

    # Functions to load data


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
    '''
    Returns a list of documents, {expid: 'string', fivedose_nsc: number}
    The expid field is repeated as there are many NSCs in each experiment
    '''
    ids = [d for d in
           (dataService.FIVEDOSE_COLL.aggregate(
               [
                   {
                       '$project': {
                           'expid': 1,
                           'nsc': '$tline.nsc',
                           '_id': 0
                       }
                   }, {
                   '$unwind': {
                       'path': '$nsc'
                   }
               }, {
                   '$group': {
                       '_id': {
                           'expid': '$expid'
                       },
                       'nsc': {
                           '$addToSet': '$nsc'
                       }
                   }
               }, {
                   '$project': {
                       'expid': '$_id.expid',
                       'nsc': 1,
                       '_id': 0
                   }
               }
               ]
           ))
           ]
    uniques = []
    nsc_dict = {}
    for x in ids:
        uniques.append(x['expid'])
        nsc_dict[x['expid']] = x['nsc']
    uniques.sort()
    return uniques, nsc_dict


def get_invivo_expids():
    data = dataService.INVIVO_COLL.aggregate([
        {
            '$project': {
                'exp_nbr': 1,
                'invivonsc': 1,
                '_id': 0
            }
        }
    ])
    data = [d for d in data]
    invivo_dict = {}
    for invivo in data:
        try:
            nscs = invivo['invivonsc'].replace('\'', '').split(',')
            nscs = [int(x) for x in nscs]
            invivo_dict[str(invivo['exp_nbr'])] = nscs
        except KeyError:
            continue
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
        dbc.NavItem(dbc.NavLink("Five Dose", active="exact", href="/fivedose", id='fivedose-nav')),
        dbc.NavItem(dbc.NavLink("One Dose", active="exact", href="/onedose", id='onedose-nav')),
        dbc.NavItem(dbc.NavLink("Invivo", active="exact", href="/invivo", id='invivo-nav')),
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
        dcc.Store(id='app-store'),
        html.Div(id='initializer')
    ]
)
# +++++++++++++++++++++++++++++++++++++++++++++++++++


# ********** Start The server Here **********
if __name__ == '__main__':
    app.run_server(debug=True)
# *******************************************
