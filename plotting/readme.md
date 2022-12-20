# Plotly and Dash
## Description

The purpose of this codebase is to serve as a proof of concept for graphing using the aforementioned frameworks with respect to MongoDB and the DW task.
## Installation
### .env file

The .env file requires values for the following:


`CONN_STRING=mongodb+srv://<username>:<password>@<url>/?retryWrites=true&w=majority`

`USERNAME=<Oracle Username>`

`PW=<Oracle Password>`

`HOST=<Oracle Host>`

`SERVICE=<Oracle Service>`

## Libraries
    Plotly
    Pandas
    Dash
    Dash Bootstrap Components
    Dotenv
    Pymongo
    Oracledb
    SqlAlchemy

## Execution
`python app.py`

The Dash framework will create a Flask server running on your local host.


