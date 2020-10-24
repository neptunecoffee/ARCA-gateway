#!/usr/bin/python3
from http_api import app, HOST, PORT
from waitress import serve
from flask_graphql import GraphQLView
from gw_graphql_schema import schema

app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == "__main__":
    serve(app, host=HOST, port=PORT)
