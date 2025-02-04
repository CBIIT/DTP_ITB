import pickle
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px

# Load the pickle file
with open('refined_metrics.pkl', 'rb') as file:
    refined_metrics = pickle.load(file)

# Load the pickle file
with open('mlflow_genai_responses.pkl', 'rb') as file:
    genai_responses = pickle.load(file)

# Load the other pickle file
with open('export_table.pkl', 'rb') as file:
    eval_data = pickle.load(file)

# Restructure Eval Data
# I am a stable genius.
eval_dict = {}
for eval_dat in eval_data:
    k = list(eval_dat.keys())[0]
    eval_dict[k] = eval_dat[k]

# Initialize the Dash app
app = dash.Dash(__name__)

# Create the layout
app.layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='metric-dropdown',
            options=[{'label': key, 'value': key} for key in refined_metrics.keys()],
            value=list(refined_metrics.keys())[0],
            style={'width': '90%', 'margin': '10px'}
        ),
        dcc.Dropdown(
            id='column-dropdown',
            style={'width': '90%', 'margin': '10px'}
        )
    ], style={'width': '20%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),
    html.Div([
        html.H2(id='selected-metric-title', style={'text-align': 'center'}),
        dcc.Graph(id='metric-graph', style={'width': '90%', 'margin': '0 auto'}),
        dash_table.DataTable(
            id='response-table',
            style_cell={'textAlign': 'left', 'minWidth': '150px', 'maxWidth': '150px', 'whiteSpace': 'normal'},
            style_data={'whiteSpace': 'normal', 'height': 'auto'}
        )
    ], style={'width': '75%', 'display': 'inline-block', 'padding': '10px', 'text-align': 'center'})
], style={'display': 'flex', 'justify-content': 'space-between'})

# Callback to update the column dropdown and title based on the selected metric
@app.callback(
    [Output('selected-metric-title', 'children'),
     Output('column-dropdown', 'options'),
     Output('column-dropdown', 'value')],
    [Input('metric-dropdown', 'value')]
)
def update_column_dropdown(selected_metric):
    df = refined_metrics[selected_metric]
    column_options = [{'label': col, 'value': col} for col in df.columns]
    return selected_metric, column_options, df.columns[0]

# Callback to update the graph based on the selected column
@app.callback(
    Output('metric-graph', 'figure'),
    [Input('metric-dropdown', 'value'),
     Input('column-dropdown', 'value')]
)
def update_graph(selected_metric, selected_column):
    df = refined_metrics[selected_metric]
    fig = px.bar(df, x=df.index, y=selected_column, title=f"{selected_column}")
    fig.update_layout(
        xaxis_title="Evaluation Metrics",
        yaxis_title="Score",
        yaxis=dict(range=[0, 1]),
        title_x=0.5  # Center the title
    )
    return fig

# Callback to update the table based on the selected metric
@app.callback(
    [Output('response-table', 'data'),
     Output('response-table', 'columns')],
    [Input('metric-dropdown', 'value'),
     Input('column-dropdown', 'value')]
)
def update_table(selected_metric, selected_column):
    data = eval_dict[selected_metric] # dataframe
    s_data = pd.DataFrame(data[selected_column])
    s_data.reset_index(inplace=True)
    s_data_exp = s_data.to_dict('records')
    columns = [{'name': col, 'id': col} for col in s_data.columns]
    columns = [{'name': 'Eval Params', 'id': 'index'}, {'name': f'Field: {selected_column}', 'id': selected_column}]
    return s_data_exp, columns

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
