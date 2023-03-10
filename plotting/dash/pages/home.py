import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/')

layout = dbc.Row(
    [
        dbc.Col(width=4),
        dbc.Col(
            dbc.Carousel(
                items=[
                    {"key": "1", "src": "https://consumer.healthday.com/media-library/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbWFnZSI6Imh0dHBzOi8vYXNzZXRzLnJibC5tcy8zMjY4Nzk4MC9vcmlnaW4uanBnIiwiZXhwaXJlc19hdCI6MTcxNTc3NjUyNH0.-UPomGM0Fc921w7c4pyk72H5oys1duLxBxlY3WIrZKc/image.jpg?width=1245&height=700&quality=85&coordinates=0%2C58%2C0%2C58"},
                    {"key": "2", "src": "https://consumer.healthday.com/media-library/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbWFnZSI6Imh0dHBzOi8vYXNzZXRzLnJibC5tcy8yNjU5MTY1NC9vcmlnaW4uanBnIiwiZXhwaXJlc19hdCI6MTY4NDgwMTM0Nn0.k3vPP3D1k6XmovZ6fNxNpVTlG2bClb9ZmXR0gFvDpT4/image.jpg?width=1245&height=700&quality=85&coordinates=0%2C92%2C0%2C92"},
                    {"key": "3", "src": "https://consumer.healthday.com/media-library/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpbWFnZSI6Imh0dHBzOi8vYXNzZXRzLnJibC5tcy8yNzU3NDMzOC9vcmlnaW4uanBnIiwiZXhwaXJlc19hdCI6MTcxNjA5MDgwMn0.rJKAEELb9WlrJ5B80UgZqCASXcJk1ba-gLxJyCev9yU/image.jpg?width=1245&height=700&quality=85&coordinates=0%2C0%2C0%2C0"},
                ],
                controls=False,
                indicators=False,
                interval=2000,
                ride="carousel"
            ),
            width=4
        ),            
        dbc.Col(width=4)
    ]
)
