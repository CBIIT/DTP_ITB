# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
# app.py is the driver of the application and orchestrates the integration
# of all the other parts of the graphing application.

from dash import Dash, html, dcc, Output, Input
import dash
import dash_bootstrap_components as dbc
from pages.dataservice import dataService

# The variable, app, is the object containing the application.
# use_pages means all routes in the pages folder will be scanned and added.
# title represents the browser bar title name.
# external_stylesheets indicates the list of css files included as well as those in the assets folder
# meta_tags represent standard HTML head meta configuration settings
# suppress_callback_exceptions is enabled because of how dynamic certain parts of the application are
#           for example, portions of pages are rendered depending on conditions, some of which
#           have event (callback) listeners attached to properties, which, at start and run time,
#           can't be mapped in the initial phase of the application lifecycle.
app = Dash(
    __name__,
    use_pages=True,
    title='DCTD Data Plots',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    suppress_callback_exceptions=True
)


# Initialize the shared data and store it in dcc.store
# This is a refactoring adventure to simplify DataService
@app.callback(
    Output('app-store', 'data'),
    Output('initializer', 'children'),
    Input('initializer', 'style')
)
def initialize(_):
    '''
    This initially loads values for the dropdowns on the various pages to help simulate
    the fact that every expid or nsc was not pre-loaded, only a certain part of it.
    I have arbitrarily picked 25 values from each of the collections to help bootstrap it.
    :param _:
    :return:
        dict: data_dict contains all values that were initialized.
            static keys: 'fd_dict' for 5 dose, 'compounds' for compounds,
                'invivo_dict' for invivo experiments, 'onedose_dict' for one dose expids
                'nci_60_fd' for all the nci 60 cells and their respective expids. This is not functional
                right now.
    '''
    data_dict = {'fd_dict': load_exp_ids()}
    # TODO:Refactor all of this to autocomplete
    print(f'Five dose exp ids loaded...')

    data_dict['compounds'] = load_comps()
    print(f'Compound NSCs loaded...')

    data_dict['invivo_dict'] = get_invivo_expids()
    print(f'Invivo Exp Nbrs loaded...')

    data_dict['onedose_dict'] = get_od_expids()
    print(f'One Dose expIds loaded...')

    data_dict['nci_60_fd'] = get_fd_cells()
    return data_dict, ''

    # Functions to load data


def get_fd_cells():
    """
    Originally used to pivot having NCI60 cell lines as the keys for all experiments, but, under development.
    :return: list: empty list until revisited
    """
    return []
    # return [d['_id'] for d in
    #       (dataService.CELLS_COLL.aggregate(
    #          [
    #              {
    #                  '$project': {
    #                      '_id': 1,
    #                      'results': 0
    #                  }
    #             }, {
    #                  '$limit': 25
    #             }
    #         ]
    #     ))
    #      ]


def load_comps():
    """
    Gathers all compounds that have SMILES, Chem name, and a preferred name field.
    :return: list: list of compounds that meet requirements
    """
    return [d for d in
            (dataService.COMPOUNDS_COLL.aggregate([
                {
                    '$match': {
                        'mv_dtp_disregistration_short': {
                            '$exists': True
                        },
                        'cmpd_chem_name': {
                            '$exists': True
                        },
                        'preferred_name': {
                            '$exists': True
                        }
                    }
                }, {
                    '$project': {
                        '_id': 0,
                        'nsc': 1,
                        'name': '$preferred_name'
                    },
                }, {
                    '$unwind': {
                        'path': '$name'
                    }
                }, {
                    '$limit': 25
                }
            ]))
            ]


def load_exp_ids():
    """
    Gathers Five Dose experiment IDs. Just the first 25
    :return: list: 25 experiment IDs to initially populate dropdowns.
    """
    fd = {}
    data = [fd.update({d['expid']: fd_helper(d['fivedosensc'])}) for d in
            dataService.FIVEDOSE_COLL.aggregate([
                {
                    '$project': {
                        'expid': 1,
                        'fivedosensc': 1,
                        '_id': 0
                    }
                }, {
                    '$limit': 25
                }
            ])
            ]
    return fd


def fd_helper(d):
    """
    For documents that have nsc lists in total string format, this creates a list of those NSCs
    :param d: string: string representation of the NSC list
    :return: list: list of all NSCs in the experiment.
    """
    return [int(d) for d in d.replace('\'', '').split(',')]


def get_invivo_expids():
    """
    Return first 25 invivo experiments with a list of the NSCs tested as the value of each expid key.
    :return: dict: first 25 invivo experiment ids and list of NSCs in the experiment
    """
    data = dataService.INVIVO_COLL.aggregate([
        {
            '$project': {
                'expid': 1,
                'invivonsc': 1,
                '_id': 0
            }
        }, {
            '$limit': 25
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
    """
    Returns a dictionary of one dose experiment IDs and associated NSCs in that experiment
    :return: dict: experiment ID : list: NSCs used in experiment
    """
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


# Navigation Bar with each route
# pills is a styling technique to highlight the current, active route
# navbar is a toggle to the rendering engine to specify that this is a navigation bar
nav = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Home", active="exact", href="/", id='home-nav')),
        dbc.NavItem(dbc.NavLink("Compounds", active="exact", href="/comps", id='comps-nav')),
        dbc.NavItem(dbc.NavLink("Invivo", active="exact", href="/invivo", id='invivo-nav')),
        dbc.NavItem(dbc.NavLink("Five Dose", active="exact", href="/fivedose", id='fivedose-nav')),
        dbc.NavItem(dbc.NavLink("One Dose", active="exact", href="/onedose", id='onedose-nav')),
        dbc.NavItem(dbc.NavLink("OncoKB", active="exact", href="/oncokb", id='oncokb-nav')),
        dbc.NavItem(dbc.NavLink("By Cell", active="exact", href="/cells", id='cells-nav'))

    ],
    pills=True,
    navbar=True
)

# The layout is the root of the application and its child pages. The navbar will be present at all times,
# but the page_container_id section will represent the various pages of the application as they are
# routed.
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


# ********** Start The server Here **********
# debug enables a page debug section that helps with exceptions and other errors
if __name__ == '__main__':
    app.run_server(debug=True)
# *******************************************
