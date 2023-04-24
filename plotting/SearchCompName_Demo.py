import pymongo
import dash
from dash import html
from dash import dcc
from dash import dash_table
from dash.dependencies import Input, Output

# Emily Zhou, 04/23/2023
# This script connects to MonogDB compounds collection; the user can enter a search compound name text, and the app returns a drop down list of NSCs and corresponding compound names.
# Once a user selects a NSC from the dropdown list, the app searches all the expids (from the five-dose collection) for the selected NSC. 

# Connect to MongoDB
client = pymongo.MongoClient('mongodb+srv://user:password@ncidctdcluster.hypf0.mongodbgov.net/NCIDCTD')
db_name = 'NCIDCTD'
db = client[db_name]

col = db['compounds']

# Define the Dash app
# app = dash.Dash(__name__)
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Search Compounds"),
    dcc.Input(id="search-box", type="text", placeholder="Enter search term"),
    html.Button("Search", id="search-button"),
    html.Br(),
    html.Div(id="results"),
    dcc.Dropdown(id="nsc-dropdown-dummy", options=[], placeholder="Select a NSC number dummy", style={"display": "none"}),
    dcc.Dropdown(id="expid-dropdown", options=[], placeholder="Select an expid")
])


# Define the callback function for the search button
@app.callback(
    Output("results", "children"),
    Input("search-button", "n_clicks"),
    Input("search-box", "value")
)
def search_compounds(n_clicks, search_term):
    if not search_term:
        return None

    if n_clicks is not None and n_clicks > 0:
        query = [
            {"$match": {"cmpd_chem_name.name": {"$regex": ".*" + search_term + ".*", "$options": "i"}}},
            {"$unwind": "$cmpd_chem_name"},
            {"$match": {"cmpd_chem_name.name": {"$regex": ".*" + search_term + ".*", "$options": "i"}}},
            {"$project": {"_id": 0, "nsc": 1, "name": "$cmpd_chem_name.name"}},
            {"$sort": {"nsc": 1}}
        ]

        results = list(col.aggregate(query))

        if not results:
            return "No results found"

        # Extract the unique NSC numbers
        nsc_list = list(set([result["nsc"] for result in results]))

        # Create the NSC dropdown options
        nsc_options = sorted([{"label": str(nsc), "value": int(nsc)} for nsc in nsc_list],
                             key=lambda x: int(x["value"]))

        # Create the NSC dropdown component
        nsc_dropdown = dcc.Dropdown(
            id="nsc-dropdown",   options=nsc_options,   placeholder="Select a NSC number"
        )

        # Combine the results and dropdown components into a single HTML element
        return html.Div([
            html.Br(),
            nsc_dropdown,
            html.Br(),
            dash_table.DataTable(
                id="results-table",
                columns=[{"name": "NSC", "id": "nsc"}, {"name": "Name", "id": "name"}],
                data=results,
                style_cell={"textAlign": "left"}
            )
        ])


# Define the callback function for the NSC dropdown
@app.callback(
    Output("expid-dropdown", "options"),
    Input("nsc-dropdown", "value")
)
def update_expids(selected_nsc):
    if not selected_nsc:
        return []

    selected_nsc_int = int(selected_nsc)

    query = {"tline.nsc": selected_nsc_int}
    projection = {"_id": 0, "expid": 1}

    print("Running expid query in update_expids function : ", query)

    expids = db.fivedose.distinct("expid", query)

    print(expids)

    options = [{"label": str(expid), "value": str(expid)} for expid in expids]

    return options

if __name__ == '__main__':
    app.run_server(debug=True)