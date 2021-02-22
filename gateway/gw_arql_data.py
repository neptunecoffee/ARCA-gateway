#!/usr/bin/python3
from http_api import connect_to_database, MONGO_STRING, DB_NAME, TRANSACTIONS_COLLECTION, BLOCKS_COLLECTION
from pymongo.errors import ConnectionFailure
from time import time

TIME_LIMT_QUERY_EXEC_MS = 60000

def get_transaction(tx_id):
    try:
        db = connect_to_database(MONGO_STRING, DB_NAME)
        tx_collection = db[TRANSACTIONS_COLLECTION]
        tx = tx_collection.find_one({"id" : tx_id},{"id" : 1, "tags" : 1, "height" : 1, "timestamp" : 1})
        if tx is not None:
            if "tags" in tx:
                for tag in tx["tags"]:
                    if "name" in tag and "value" in tag:
                        if hasattr(tag["name"],"decode"):
                            string_name = tag["name"].decode("UTF-8","backslashreplace")
                            tag["name"] = string_name
                        if hasattr(tag["value"],"decode"):
                            string_value = tag["value"].decode("UTF-8","backslashreplace")
                            tag["value"] = string_value
    except ConnectionFailure as e:
        print("Could not connect to database:", e)
    return tx

def get_transactions(**kwargs):
    """
    This function takes up to 3 optional parameters: <from> (DB: owner_address), <to> (DB: target), <tags> (DB: tags)
    and includes into the query only those that are set, returning the transactions that match the criteria.
    """
    query_list = []
    query_criteria = {}
    if "from" in kwargs:
        from_owner = kwargs["from"]
        query_owner = {}
        query_owner["owner_address"] = from_owner
        query_list.append(query_owner)
    if "to" in kwargs:
        to = kwargs["to"]
        query_target = {}
        query_target["target"] = to
        query_list.append(query_target)
    if "tags" in kwargs:
        tags = kwargs["tags"]
        for tag in tags:
           flag = False
           query_tags  = {}
           query_tags_pair = {}
           if "name" in tag:
                flag = True
                if hasattr(tag["name"],"encode"):
                    query_tags_pair["tags.name"] = tag["name"].encode("UTF-8","backslashreplace")
                else:
                    query_tags_pair["tags.name"] = tag["name"]
           if "value" in tag:
               flag = True
               if hasattr(tag["value"],"encode"):
                   query_tags_pair["tags.value"] = tag["value"].encode("UTF-8","backslashreplace")
               else:
                   query_tags_pair["tags.value"] = tag["value"]
           if not flag:
               raise Exception("No 'name' or 'value' fields were given in a tag in tags list, cannot perform search in DB.")
           query_list.append(query_tags_pair)
        if not tags:
           query_tags = {}
           query_tags["tags"] = []
           query_list.append(query_tags) 
    if not query_list:
        return None
    else:
        query_criteria["$and"] = query_list
    try:
        db = connect_to_database(MONGO_STRING, DB_NAME)
        tx_collection = db[TRANSACTIONS_COLLECTION]
        txs = tx_collection.find(query_criteria, {"id" : 1, "owner_address" : 1, "target" : 1, "tags" : 1}).max_time_ms(TIME_LIMT_QUERY_EXEC_MS)
        return txs
    except ConnectionFailure as e:
        print("Could not connect to database:", e)
