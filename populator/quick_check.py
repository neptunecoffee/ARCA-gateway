#!/usr/bin/env python3

import pymongo
import time
import random
from multiprocessing.dummy import Pool as ThreadPool
import requests
import sys
import multiprocessing

MONGO_STRING="mongodb://127.0.0.1:27017"
MONGO_DB="arweave"
MAX_BLOCK=492769

def mongo_connect(col):
    try:
        conn = pymongo.MongoClient(MONGO_STRING)
        db=conn[col]
        print("Connected successfully!")
    except Exception as ex:
        print(ex)
        print("Could not connect to MongoDB")
        exit()
    return db

def main():
    t1=time.time()
    db=mongo_connect(MONGO_DB)
    for i in range(0,MAX_BLOCK+1):
        r=db.blocks.find_one({"height":i})
        print(r["height"])
        for j in r["txs"]:
            print(j)

if __name__ == "__main__":
    main()
