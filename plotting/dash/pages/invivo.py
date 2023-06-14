"""
Invivo experiments are selected and data plots are displayed.

As of 6/2/2023 this section needs to be updated due to a new data model, and additional approaches on plots.
As of 6/13/2023 this section has been reworked a bit, but the case of looking at individual animals
    per group might not be useful-- or needs to be addressed so as not to interfere with navigation from
    compounds list link.
Additional Notes:
    - Experiments that were completed at two separate times (ie JXJ2-1) and have a control create a total
      anomaly for navigation. We end up with a list of NSC 999999 listed twice. the graphs themselves are
      skewed a bit, but normalized based on implant and staging timelapses. If we use exact dates, then,
      it would create a huge X-axis range. Instead, we are using observation time relative to the distance
      from implant date (or stage date, as I forget at this moment). This still leaves the issue of repeated
      NSCs and the underlying data associated with that group. Perhaps labeling as 1a and 1b might do it.
"""
import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
from .dataservice import dataService
from dash.exceptions import PreventUpdate

dash.register_page(__name__, path='/invivo', path_template='/invivo/<expid>/<nsc>')

ROW_PADDING = {
    "paddingTop": "calc(var(--bs-gutter-x) * .5)",
    "paddingBottom": "calc(var(--bs-gutter-x) * .5)"
}


def get_left_select(expid, nsc):
    """
    The left select for menus associated with invivo experiments. Modified to handle dynamic URLs
    :param expid: string: the expid for given experiment
    :param nsc: string: NSC selected from compounds list
    :return: dcc.Component: html.Div that contains the various components of the left-select section
    """
    if expid is None and nsc is None:
        expid_dropdown = dcc.Dropdown(id="s-expid-dropdown", placeholder="Select Experiment ID")
        exp_dropdown = dcc.Dropdown(id="s-exp-dropdown", disabled=True)
        groups = dbc.Select(id="s-group-dropdown", disabled=True)
    else:
        experiments = dataService.get_invivo_experiment_nbrs(expid)
        expid_dropdown = dcc.Dropdown(id="s-expid-dropdown", value=expid, options=[{'label': expid, 'value': expid}])
        exp_dropdown = dcc.Dropdown(id="s-exp-dropdown",
                                    placeholder='Select Experiment No',
                                    options=[{'label': exp['exp_nbr'], 'value': exp['exp_nbr']} for exp in experiments]
                                    )
        groups = dbc.Select(id="s-group-dropdown", disabled=True)

    return dbc.Card(body=True, children=[
        html.Div(id='input-form-div', children=[
            dbc.Form(id='input-form', children=[
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment ID", html_for="s-expid-dropdown"),
                        expid_dropdown
                    ])
                ], style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Experiment Number", html_for="s-exp-dropdown"),
                        exp_dropdown
                    ])
                ], style=ROW_PADDING),
                dbc.Row(children=[
                    html.Div(className='d-grid', children=[
                        dbc.Label("Select Group Number", html_for="s-group-dropdown"),
                        groups
                    ])
                ], style=ROW_PADDING)
            ])
        ])
    ])


@dash.callback(
    Output("s-expid-dropdown", "options"),
    Input("invivo-nav", "id"),
    State("app-store", "data"),
    prevent_initial_call=True
)
def initialize(nav, data):
    """
    Populate the experiment ID dropdowns with a small list
    :param nav: the hook to listen for navigation events to this page
    :param data: dcc.Store: the container object of pre-loaded experiment IDs
    :return: list: list of label: value dict objects to populate dropdown
    """
    print('Initialized Invivo Experiment ID dropdown')
    return [{"label": x, "value": x} for x in data['invivo_dict'].keys()]


@dash.callback(
    Output('s-expid-dropdown', 'options', allow_duplicate=True),
    Input('s-expid-dropdown', 'search_value'),
    prevent_initial_call=True
)
def update_expids_by_search(search_val):
    return [{'label': d['expid'], 'value': d['expid']} for d in dataService.INVIVO_COLL.aggregate([
        {
            '$match': {
                'expid': {'$regex': search_val}
            }
        }, {
            '$project': {
                '_id': 0,
                'expid': 1
            }

        }, {
            '$limit': 15
        }
    ])]

@dash.callback(
    Output('s-exp-dropdown', 'options'),
    Output('s-exp-dropdown', 'disabled'),
    Input('s-expid-dropdown', 'value'),
    prevent_initial_call=True
)
def get_exp_nos(expid):
    experiments = dataService.get_invivo_experiment_nbrs(expid)
    return [{'label': exp['exp_nbr'], 'value': exp['exp_nbr']} for exp in experiments], False


@dash.callback(
    Output(component_id='s-group-dropdown', component_property='options'),
    Output(component_id='s-group-dropdown', component_property='disabled'),
    Input(component_id='s-exp-dropdown', component_property='value'),
    State("s-expid-dropdown", "value"),
    prevent_initial_call=True
)
def handle_group_no_selections(exp, expid):
    """
    This is a messy function that is supposed to handle form validation and selection processing of the left
    select dropdowns.
    :param expid: string: currently selected experiment ID
    :param data: dcc.Store: application-wide data storage object for various data
    :return: list, boolean, list, boolean: list of NSCs, enable state of nsc dropdown, list of groups, enabled state of
                group number dropdown
    """

    if ctx.triggered[0]['prop_id'] == 's-expid-dropdown.value':
        if ctx.triggered[0]['value'] is None:
            raise PreventUpdate

    group_nbrs = dataService.get_invivo_group_numbers(exp, expid)
    group_labels = [{"label": x + 1, "value": x} for x in group_nbrs]

    return group_labels, False

    # ------------- OLD CODE IS BELOW ------------------------

    # Checks to see which Input was changed using the 'changed' context trigger ID, and handles request
    if expid is not None:
        # this is a best first attempt at handling NSCs that are actually control values. Passes NSC list back
        return [{"label": "Control", "value": x} if (x == 999999) else {"label": x, "value": x} for x in
                nscs], False, [], True  # , [{"label": expid, "value": expid}]
    elif (changed == 's-nsc-dropdown') and (expid is not None):
        group_nbrs = dataService.get_invivo_group_numbers(nsc, expid)
        group_labels = [{"label": "1 - Control", "value": x} if (x == 0) else {"label": x + 1, "value": x} for x in
                        group_nbrs]
        # returns all menu optops filled out along with enabled group number dropdowns
        return [{"label": "Control", "value": x} if (x == 999999) else {"label": x, "value": x} for x in
                nscs], False, group_labels, False  # , [{"label": expid, "value": expid}]
    else:
        # This case is unlikely, but here for handling
        return ['error'], True, ['error'], True


@dash.callback(
    Output(component_id='s-graph-content', component_property='children'),
    Input(component_id="s-graph-tabs", component_property="active_tab"),
    Input(component_id='s-group-dropdown', component_property='value'),
    State(component_id='s-exp-dropdown', component_property='value'),
    State(component_id='s-expid-dropdown', component_property='value')
)
def get_graphs(active_tab, group, exp, expid):
    """
    Facilitates the process of generating the graphs and wrapping them in component object containers to be rendered.
    :param active_tab: string: the currently selected tab
    :param group: int: the currently selected group number
    :param exp: int: the selected NSC
    :param expid: string: the experiment ID searched on
    :return: dcc.Component: container of a set of plots to be rendered
    """
    changed = ctx.triggered_id
    if (group is None) or (not ctx.triggered):
        return html.P('Please select Exp Nbr, NSC, and Group')
    else:
        # The summary tab displays similarly to the supplier report for invivo with box plots for each group
        # and a table describing the treatment and composition of the groups.
        if active_tab == 'summ-tab':
            return get_summary_components(expid, exp)
        # This creates a Kaplan-Meier curve for a given group along with the control group
        if active_tab == 'survival-tab':
            return dcc.Graph(figure=dataService.get_km_graph(expid, group))
        # This creates scatter-line plots of net weight and tumor weight
        if active_tab == 'average-tab':
            figures = dataService.get_anml_weight_graphs(expid, exp, group)

            # Keys are weight and tumor
            graphs = [
                dbc.Row(dcc.Graph(figure=figures['weight'])),
                dbc.Row(dcc.Graph(figure=figures['tumor']))
            ]
            return graphs
        # This creates boxplots for the groups over the period of time
        if active_tab == 'boxes-tab':
            figures = dataService.get_invivo_box_plots(expid, exp, group)

            graphs = [
                dbc.Row(dcc.Graph(figure=figures['weight'])),
                dbc.Row(dcc.Graph(figure=figures['tumor']))
            ]
            return graphs
        return html.P('Please select Exp Nbr, NSC, and Group')


def get_summary_components(expid, nsc):
    """
    Function to generate the components to replicate a supplier reports invivo page. Made into separate function for
    clarity.
    :param expid: string: The experiment ID
    :param nsc: string: the NSC
    :return: list: dash components containing the graphs and table for look and feel of summary report
    """
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


def layout(expid=None, nsc=None):
    """
    Layout object that is the main wrapper of this whole module. Function to handle dynamic URL patterns
    :param expid: string: the experiment ID
    :param nsc: string: the NSC selected from compounds list
    :return: dbc.Row: a dash bootstrap component Row containing all the section content.
    """
    if expid is None and nsc is None:
        card_body = html.Div(html.P('Please select Exp Nbr, NSC, and Group'), id='s-graph-content')
    else:
        card_body = html.Div(get_summary_components(expid, nsc))
    return dbc.Row(children=[
        dbc.Col(get_left_select(expid, nsc), width=2),
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
                                     children=card_body))
        ]), width=10
        )
    ], style=ROW_PADDING)
