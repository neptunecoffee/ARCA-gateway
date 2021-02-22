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
    +ids, +blocks, owners instead <from>, recipients instead <to>, sort (sort_order: enum...)
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
        if not "_in" in block:
            in_height_list = []
        else:
            in_height_list = block["_in"]
        '''
        The following are just nested dicts and lists for a query searching for txs that have their block height either in a list of specified heights: 
        block[_in] or in a min to max interval. The per se query is:
        {"$or":[ {"height":{"$in":in_height_list}}, {"$and":[ {"height":{"$lte":max}}, {"height":{"$gte":min}} ]} ]}
        '''
        query_height = {}
        query_height_in = {}
        height_in = {}
        lt_part = {}
        gt_part = {}
        height_lt = {}
        height_gt = {}
        and_list = []
        or_list = []
        query_and = {}
        query_or = {}
        height_in["$in"] = in_height_list
        query_height_in["height"] = height_in
        or_list.append(query_height_in)
        lt_part["$lte"] = max
        gt_part["$gte"] = min
        height_lt["height"] = lt_part
        height_gt["height"] = gt_part
        and_list.append(height_lt)
        and_list.append(height_gt)
        query_and["$and"] = and_list
        or_list.append(query_and)
        query_height["$or"] = or_list
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
        add to query_list an { 'tags.name':name, 'tags.value':{op=$in/$nin:[...values..]} } element for each TagFilter
        '''
        for tag in tags:
           query_tags = {}
           flag = False
           query_tags_pair = {}
           op_values = {}
           if "name" in tag:
                flag = True
                if hasattr(tag["name"],"encode"):
                    query_tags_pair["name"] = tag["name"].encode("UTF-8","backslashreplace")
                else:
                    query_tags_pair["name"] = tag["name"]
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
               query_tags_pair["value"] = op_values
           if not flag:
               raise Exception("No 'name' or 'value' fields were given in a tag in tags list, cannot perform search in DB.")
           query_tags["tags"] = query_tags_pair
           query_list.append(query_tags)
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
        print(query_criteria)
        ''' 
        txs = tx_collection.find(query_criteria, {"id" : 1, "last_tx" : 1, "signature" : 1, "owner_address" : 1 , "owner" : 1, "target" : 1,
                  "reward" : 1, "quantity" : 1,  "height" : 1, "tags" : 1, "_id":0}
              ) #.sort("height",sort_direction).max_time_ms(TIME_LIMT_QUERY_EXEC_MS)
        '''
        txs = tx_collection.find(query_criteria).max_time_ms(TIME_LIMT_QUERY_EXEC_MS)
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


if __name__ == "__main__":
    #tx = get_transaction("-wvMzOoelFkC_YxxpeglpYGcYTt-OaLvLVDhCca2HTM")
    #print("tx[anchor]=", tx["last_tx"])
    #block = get_block(height=109876)
    block = get_block(id="pi-SmSkICWUTMMl5lBBAynhROV1OP9m68NZ6t9ZzLePmLexfuWhQk-UwNgsbYZNp")
    #block = 
    print("Block info: height= ", block["height"], "id=", block["indep_hash"])
    print("timestamp= ", block["timestamp"])
    print("prevous b ID= ", block["previous"])
