#!/usr/bin/python3
from http_api import connect_to_database, MONGO_STRING, DB_NAME, TRANSACTIONS_COLLECTION, BLOCKS_COLLECTION
from pymongo.errors import ConnectionFailure
import pymongo
from time import time

TIME_LIMT_QUERY_EXEC_MS = 60000
DEFAULT_FIRST = 10

def get_max_block_height():
    try:
        db = connect_to_database(MONGO_STRING, DB_NAME)
        blocks_collection = db[BLOCKS_COLLECTION]
        height_bks = blocks_collection.find({"height":{"$ne":None}},{"height":1}).sort("height",pymongo.DESCENDING)
    except ConnectionFailure as e:
        print("Could not connect to database:", e)
    max_height = -1
    for bk in height_bks:
        if "height" in bk:
            max_height = bk["height"]
            break
    return max_height

def get_transaction(tx_id):
    try:
        db = connect_to_database(MONGO_STRING, DB_NAME)
        tx_collection = db[TRANSACTIONS_COLLECTION]
        tx = tx_collection.find_one({"id" : tx_id},{"id" : 1, "last_tx" : 1, "signature" : 1, "target" : 1, "owner" : 1, "owner_address" : 1, "reward" : 1,
                                      "quantity" : 1, "tags" : 1, "height" : 1, "timestamp" : 1
             })
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
    This function takes up to  optional parameters: <owners>, a list of owner addresses (DB: owner_address), <recipients> a list of targets(DB: target),
    <ids>, a list of transactions ids, <tags> (DB: tags), a list of filters by name and values,.....,<first>
    and includes into the query only those that are set, returning the transactions that match the criteria.
    """
    query_list = []
    query_criteria = {}
    sort_direction = -1
    if "sort" in kwargs:
        if kwargs["sort"] == 1:
            sort_direction = 1
    if "ids" in kwargs:
        ids = kwargs["ids"]
        query_ids = {}
        query_in = {}
        query_in["$in"] = ids
        query_ids["id"] = query_in
        query_list.append(query_ids)
    if "block" in kwargs:
        block = kwargs["block"]
        if not "min" in block:
            min = 0
        else:
            min = block["min"]
        if not "max" in block:
            if "min" in block:
                max = get_max_block_height()
            else:
                max = -1
        else:
            max = block["max"]

        query_height = {}
        lt_part = {}
        gt_part = {}
        height_lt = {}
        height_gt = {}
        and_list = []
        query_and = {}
        lt_part["$lte"] = max
        gt_part["$gte"] = min
        height_lt["height"] = lt_part
        height_gt["height"] = gt_part
        and_list.append(height_lt)
        and_list.append(height_gt)
        query_height["$and"] = and_list
        query_list.append(query_height)
    if "owners" in kwargs:
        owners = kwargs["owners"]
        query_owners = {}
        intermediary_q = {}
        intermediary_q["$in"] = owners
        query_owners["owner_address"] = intermediary_q
        query_list.append(query_owners)
    if "recipients" in kwargs:
        recipients = kwargs["recipients"]
        query_target = {}
        aux_query = {}
        aux_query["$in"] = recipients
        query_target["target"] = aux_query
        query_list.append(query_target)
    if "tags" in kwargs:
        tags = kwargs["tags"] #{TagFilter: name: values:[] op:TagOperator ->'$in'/'$nin' << regarding the tags.values >>}
        '''
        '$and' : [ {filter#1}, {filter#2}, {filter#3}...{filter#n} ]
        which can be written also as '$and': [ { 'tags.name':name, 'tags.value':{op=$in/$nin:[...values..]} },{ similar_expression_for_filter#2 }, ... ]
        '''
        query_tags = {}
        query_tags_list = []
        for tag in tags:
           flag = False
           query_tags_pair = {}
           op_values = {}
           if "name" in tag:
                flag = True
                if hasattr(tag["name"],"encode"):
                    query_tags_pair["tags.name"] = tag["name"].encode("UTF-8","backslashreplace")
                else:
                    query_tags_pair["tags.name"] = tag["name"]
           if "values" in tag:
               flag = True
               input_values = tag["values"]
               values = []
               for input_value in input_values:
                   if hasattr(input_value,"encode"):
                       values.append(input_value.encode("UTF-8","backslashreplace"))
                   else:
                       values.append(input_value)
               if "op" in tag:
                   op = tag["op"]
               else:
                   op = "$in"
               op_values[op] = values
               query_tags_pair["tags.value"] = op_values
           if not flag:
               raise Exception("No 'name' or 'value' fields were given in a tag in tags list, cannot perform search in DB.")
           query_tags_list.append(query_tags_pair)
        if not tags:
           query_tags = {}
           query_tags["tags"] = []
           query_list.append(query_tags)
        else:
            query_tags["$and"] = query_tags_list
            query_list.append(query_tags)
    if not query_list:
        return None
    else:
        query_criteria["$and"] = query_list
    try:
        db = connect_to_database(MONGO_STRING, DB_NAME)
        tx_collection = db[TRANSACTIONS_COLLECTION]
        txs = tx_collection.find(query_criteria, {"id" : 1, "last_tx" : 1, "signature" : 1, "owner_address" : 1 , "owner" : 1, "target" : 1,
                  "reward" : 1, "quantity" : 1,  "height" : 1, "tags" : 1, "_id":0}
              ).sort("height",sort_direction).max_time_ms(TIME_LIMT_QUERY_EXEC_MS)
        return txs
    except ConnectionFailure as e:
        print("Could not connect to database:", e)

def get_block(**kwargs):
    '''Get a block either by height or by id (indep_hash)'''
    if "height" in kwargs:
        block_height = kwargs["height"]
        try:
            db = connect_to_database(MONGO_STRING, DB_NAME)
            blocks_collection = db[BLOCKS_COLLECTION]
            block = blocks_collection.find_one({"height" : block_height},{"indep_hash" : 1, "timestamp" : 1})
            block["height"] = block_height
        except ConnectionFailure as e:
            print("Could not connect to database:", e)
    else:
        if "id" in kwargs:
            indep_hash = kwargs["id"]
            try:
                db = connect_to_database(MONGO_STRING, DB_NAME)
                blocks_collection = db[BLOCKS_COLLECTION]
                block = blocks_collection.find_one({"indep_hash" : indep_hash},{"height" : 1, "timestamp" : 1})
                if block:
                    if "height" in block:
                        block_height = block["height"]
                    block["indep_hash"] = indep_hash
            except ConnectionFailure as e:
                print("Could not connect to database:", e)
    try:
         if block:
             prev_height = block_height -1
             prev_block = blocks_collection.find_one({"height" : prev_height},{"indep_hash" : 1})
             block["previous"] = prev_block["indep_hash"]
    except ConnectionFailure as e:
        print("Could not connect to database:", e)
    return block

def get_blocks(**kwargs):
    """
    ids = indep_hash, height, sort 
    """
    query_criteria = {}
    query_list = []
    sort_direction = -1
    if "sort" in kwargs:
        if kwargs["sort"] == 1:
            sort_direction = 1
    if "ids" in kwargs:
        ids = kwargs["ids"]
        query_ids = {}
        query_in = {}
        query_in["$in"] = ids
        query_ids["indep_hash"] = query_in
        query_list.append(query_ids)
    if "height" in kwargs:
        # {"$and":[ {"height":{"$lte":max}}, {"height":{"$gte":min}} ]}
        height = kwargs["height"]
        if not "min" in height:
            min = 0
        else:
            min = height["min"]
        if not "max" in block:
            if "min" in block:
                max = get_max_block_height()
            else:
                max = -1
        else:
            max = height["max"]
        query_height = {}
        and_list = []
        lt_part = {}
        gt_part = {}
        height_lt = {}
        height_gt = {}
        query_and = {}
        lt_part["$lte"] = max
        gt_part["$gte"] = min
        height_lt["height"] = lt_part
        height_gt["height"] = gt_part
        and_list.append(height_lt)
        and_list.append(height_gt)
        query_height["$and"] = and_list
        query_list.append(query_height)
    if not query_list:
        return None
    else:
        query_criteria["$and"] = query_list
    try:
        db = connect_to_database(MONGO_STRING, DB_NAME)
        blocks_collection = db[BLOCKS_COLLECTION]
        blocks = blocks_collection.find(query_criteria, {"indep_hash" : 1, "height" : 1, "_id":0}
             ).sort("height",sort_direction).max_time_ms(TIME_LIMT_QUERY_EXEC_MS)
        return blocks
    except ConnectionFailure as e:
        print("Could not connect to database:", e)


