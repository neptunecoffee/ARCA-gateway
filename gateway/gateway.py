#!/usr/bin/python3
from http_api import app, HOST, PORT
from waitress import serve
from flask_graphql import GraphQLView
from gw_graphql_schema import g_schema
from gw_arql_schema import ar_schema

app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view('graphql', schema=g_schema, graphiql=True))
app.add_url_rule(
        '/arql',
        view_func=GraphQLView.as_view('arql', schema=ar_schema, graphiql=True))

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == "__main__":
    serve(app, host=HOST, port=PORT)
