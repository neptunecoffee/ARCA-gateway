from flask import Flask
import pymongo
import base64
import zlib
from urllib.parse import urlparse
from flask import Response, json, jsonify, g, request
from waitress import serve

MONGO_STRING = "mongodb://127.0.0.1:27017"
DB_NAME = "arweave"
BLOCKS_COLLECTION = "blocks"
TRANSACTIONS_COLLECTION = "txs"
DATA_COLLECTION = "data"
POA_COLLECTION = "poa"
COMPRESSION_LEVEL = 3
HOST="0.0.0.0"
PORT="80"
MIME_TYPES = ["text","application", "image", "video", "audio"]
DICT = {
       "text" : ["plain", "html", "css"],
       "application" : ["octet-stream", "json", "xml", "zip"]
}

def valid_mime(mime_str):
    return True

def valid_mime_to_implement(mime_str):
    is_valid = True
    try:
        slash_index = mime_str.index("/")
        mime_type = mime_str[:slash_index].lower()
        mime_subtype = mime_str[slash_index+1:].lower()
    except:
        is_valid =  False
    if mime_type not in MIME_TYPES:
        is_valid = False
    else:
        if mime_subtype not in DICT[mime_type]:
            is_valid = False
    return is_valid

def encode_base64(data):
    url_safe_encoded_bytes = base64.urlsafe_b64encode(data)
    url_safe_encoded_str = str(url_safe_encoded_bytes, "utf-8")
    length = len(url_safe_encoded_str)
    last3_url_safe_encoded_str = url_safe_encoded_str[-3:]
    try:
        padding_index = last3_url_safe_encoded_str.index("=")
        trimmed_url_safe_encoded_str = url_safe_encoded_str[0:length-(3-padding_index)]
    except ValueError as ve:
        trimmed_url_safe_encoded_str = url_safe_encoded_str

    return trimmed_url_safe_encoded_str

def prepare_tx(tx, tx_data):
    prep_tx = tx
    if "data" not in tx_data:
        tx_data["data"] = None
    if "format" in tx:
        if tx["format"] == 2:
            prep_tx["data"] = 0
        else:
            prep_tx["data"] = encode_base64(tx_data["data"])
    else:
        prep_tx["data"] = encode_base64(tx_data["data"])
    if "signature" in tx:
        prep_tx["signature"] = tx["signature"]
    if "tags" in tx:
        encoded_tags=[]
        for tag in tx["tags"]:
            if "name" in tag:
                name = tag["name"]
            else:
                name = ""
            if "value" in tag:
                value = tag["value"]
            else:
                value = ""
            if len(name) > 0 or len(value) > 0:
                encoded_tags.append({"name": encode_base64(name), "value": encode_base64(value)})
        prep_tx["tags"] = encoded_tags
    return prep_tx

def connect_to_database(db_string, db_name):
    try:
        conn = pymongo.MongoClient(db_string)
        dbc = conn[db_name]
        print("Connected successfully!")
        return dbc
    except Exception as ex:
        print(ex)
        print("Could not connect to Database: ", db_string)
        return None

def get_db():
    if "db" not in g:
        g.db = connect_to_database(MONGO_STRING, DB_NAME)
    return g.db


app = Flask(__name__)

@app.route("/")
def index():
    o = urlparse(request.base_url)
    host = o.hostname
    if host.lower() == "subtest1.arweave.io":
        return serve_tx_content("NFU3ZxcjOJznEHmX65j0EORc3d_r_-3_p1gSqN1TAIM") 
    else:
        return "ARCA Experimental Gateway\n"

@app.route("/host")
def test():
    o = urlparse(request.base_url)
    host = o.hostname
    if host.lower() == "subtest1.arweave.io":
        serve_tx_content("NFU3ZxcjOJznEHmX65j0EORc3d_r_-3_p1gSqN1TAIM") 

@app.route("/<tx_id>")
def serve_tx_content(tx_id):
    string_data = ""
    db = get_db()
    tx_collection = db[TRANSACTIONS_COLLECTION]
    data_collection = db[DATA_COLLECTION]
    tx = tx_collection.find_one({"id" : tx_id},{"tags" : 1})
    if tx is not None:
        mime_type = "text/plain"
        if "tags" in tx:
            for tag in tx["tags"]:
                if "name" in tag and "value" in tag:
                    if hasattr(tag["name"],"decode"):
                        string_name = tag["name"].decode("UTF-8","backslashreplace")
                    else:
                        string_name = tag["name"]
                    if hasattr(tag["value"],"decode"):
                        string_value = tag["value"].decode("UTF-8","backslashreplace")
                    else:
                        string_value = tag["value"]
                    try:
                        content_index = string_name.lower().index("content-type")
                        if valid_mime(string_value):
                            mime_type = string_value
                    except ValueError as ve:
                        pass
        tx_data = data_collection.find_one({"id" : tx_id},{"data" : 1})
        if "data" in tx_data:
            if hasattr(tx_data["data"],"decode"):
                string_data = tx_data["data"].decode("UTF-8","backslashreplace")
            else:
                string_data = tx_data["data"]
        else:
            string_data = ""
        resp = Response(string_data,mimetype=mime_type,status=200)
    else:
        resp = Response("The transaction with ID " + tx_id + " was not found.", status=404)
    return resp

#/tx/<id>
#/tx/<id>/data
#/block/hash/<id>
#/block/height/<id>

@app.route("/tx/<tx_id>")
def serve_tx(tx_id):
    db = get_db()
    tx_collection = db[TRANSACTIONS_COLLECTION]
    data_collection = db[DATA_COLLECTION]
    tx = tx_collection.find_one({"id" : tx_id},{"_id":0})
    tx_data = data_collection.find_one({"id" : tx_id})
    if tx is not None:
        prepared_tx = prepare_tx(tx, tx_data)
        resp = jsonify(prepared_tx)
    else:
        resp = Response("The transaction with ID " + tx_id + " was not found.",status=404)
    return resp

@app.route("/tx/<tx_id>/data")
def serve_tx_data(tx_id):
    db = get_db()
    data_collection = db[DATA_COLLECTION]
    tx_data = data_collection.find_one({"id" : tx_id},{"data" : 1})

    if tx_data is not None:
        if "data" in tx_data:
            resp = Response(encode_base64(tx_data["data"]),status=200)
        else:
            resp = Response("Data for transaction ID = " + tx_id + " was not found.",status=404)
    else:
        resp = Response("The transaction with ID " + tx_id + " was not found.",status=404)
    return resp

@app.route("/block/hash/<block_hash>")
def serve_block_by_hash(block_hash):
    db = get_db()
    blocks_collection = db[BLOCKS_COLLECTION]
    block = blocks_collection.find_one({"indep_hash" : block_hash},{"_id" : 0})
    poa_collection = db[POA_COLLECTION]
    if block is not None:
        if "height" in block:
            height = block["height"]
            poa = poa_collection.find_one({"height" : height}, {"_id":0})
            if poa is not None and "poa" in poa:
                block["poa"] = poa["poa"]
        resp = jsonify(block)
    else:
        resp = Response("The block with hash " + block_hash + " was not found.",status=404)
    return resp

@app.route("/block/height/<int:block_height>")
def serve_block_by_height(block_height):
    db = get_db()
    blocks_collection = db[BLOCKS_COLLECTION]
    block = blocks_collection.find_one({"height" : block_height},{"_id" : 0})
    poa_collection = db[POA_COLLECTION]
    block_poa = poa_collection.find_one({"height" : block_height},{"_id" : 0})
    if block is not None:
        if block_poa is not None and "poa" in block_poa:
            block["poa"] = block_poa["poa"]
        resp = jsonify(block)
    else:
        resp = Response("The block with height " + str(block_height) + " was not found.",status=404)
    return resp

#/ziptx/<id>  headers gzip
@app.route("/ziptx/<tx_id>")
def serve_ziptx(tx_id):
    db = get_db()
    tx_collection = db[TRANSACTIONS_COLLECTION]
    data_collection = db[DATA_COLLECTION]
    tx = tx_collection.find_one({"id" : tx_id},{"_id":0})
    tx_data = data_collection.find_one({"id" : tx_id},{"_id":0})
    if tx is not None:
        prepared_tx = prepare_tx(tx, tx_data)
        zipped_tx = zlib.compress((str(prepared_tx).encode("UTF-8","backslashreplace")),COMPRESSION_LEVEL)
        resp = Response(zipped_tx, status=200, mimetype="application/zip")
    else:
        resp = Response("The transaction with ID " + tx_id + " was not found.",status=404)
    return resp

#/ziptx/<id>/data
@app.route("/ziptx/<tx_id>/data")
def serve_ziptx_data(tx_id):
    db = get_db()
    data_collection = db[DATA_COLLECTION]
    tx_data = data_collection.find_one({"id" : tx_id},{"data" : 1})

    if tx_data is not None and "data" in tx_data:
        zipped_tx_data = zlib.compress((encode_base64(tx_data["data"]).encode("UTF-8","backslashreplace")),COMPRESSION_LEVEL)
        resp = Response(zipped_tx_data, status=200, mimetype="application/zip")
    else:
            resp = Response("Data for transaction ID = " + tx_id + " was not found.",status=404)
    return resp

# /zipblock/height/<block_height>
#  In this form, a program being served should do a GET then decompress the response's content:
#     response = requests.get("http://HOST:PORT/zipblock/height/<block_height>")
#     print(zlib.decompress(response.content).decode("UTF-8"))
 
@app.route("/zipblock/height/<int:block_height>")
def serve_zipblock_by_height(block_height):
    db = get_db()
    blocks_collection = db[BLOCKS_COLLECTION]
    block = blocks_collection.find_one({"height" : block_height},{"_id" : 0})
    poa_collection = db[POA_COLLECTION]
    block_poa = poa_collection.find_one({"height" : block_height},{"_id" : 0})
    if block is not None:
        if block_poa is not None and "poa" in block_poa:
            block["poa"] = block_poa["poa"]
        zipped_block = zlib.compress((str(block).encode("UTF-8","backslashreplace")),COMPRESSION_LEVEL)
        resp = Response(zipped_block, status=200, mimetype="application/zip")
    else:
        resp = Response("The block with height " + str(block_height) + " was not found.",status=404)
    return resp

#/zipblock/hash/<block_indep_hash>
@app.route("/zipblock/hash/<block_hash>")
def serve_zipblock_by_hash(block_hash):
    db = get_db()
    blocks_collection = db[BLOCKS_COLLECTION]
    block = blocks_collection.find_one({"indep_hash" : block_hash},{"_id" : 0})
    poa_collection = db[POA_COLLECTION]
    if block is not None:
        if "height" in block:
            block_height = block["height"]
            block_poa = poa_collection.find_one({"height" : block_height},{"poa" : 1})
            if "poa" in block_poa:
                block["poa"] = block_poa["poa"]
        zipped_block = zlib.compress((str(block).encode("UTF-8","backslashreplace")),COMPRESSION_LEVEL)
        resp = Response(zipped_block, status=200, mimetype="application/zip")
    else:
        resp = Response("The block with height " + str(block_height) + " was not found.",status=404)
    return resp

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == "__main__":
    serve(app, host=HOST, port=PORT)

