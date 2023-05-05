# Plotly and Dash
## Description

The purpose of this codebase is to serve as a proof of concept for graphing using the aforementioned frameworks with respect to MongoDB and the DW task.
## Installation

The Dash application driver file is app.py. This is the root of the application. In that directory, you will need to place a .env file. This is literally a file named ".env" which will serve as the environment variable configuration file that is not to be shared outside of your personal workspace. As I have worked on the project, and eliminated the need for an Oracle database connection, the only one that remains is for MongoDB; however, if we want to connect to Oracle, that is always an option.

### .env file
The .env file requires values for the following (replace username and password fields accordingly):


`CONN_STRING=mongodb+srv://<username>:<password>@<url>/?retryWrites=true&w=majority`

## Libraries
    Plotly
    Pandas
    Dash
    Dash Bootstrap Components
    Dotenv
    Pymongo
    Lifelines
    Matplotlib (for color functions)

## Execution
`python app.py`

The Dash framework will create a Flask server running on your local host.


