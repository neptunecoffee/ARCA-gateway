#!/usr/bin/env python3

import random
import json
import time
from multiprocessing.dummy import Pool as ThreadPool
import requests
import sys
import multiprocessing
import pymongo
import functools
print = functools.partial(print, flush=True)
import base64
import hashlib
import binascii

THREADS=15
STARTING_NODE="https://arweave.net"
NETWORK_TIMEOUT=1
RETRY_DELAY=0.1
CLEANUP_INTERVAL=100
MIN_PEERS=10
MONGO_STRING="mongodb://127.0.0.1:27017"
DATABASE="arweave3"
START_BLOCK=493119
END_BLOCK=493619
MONGO_COMPRESSION="zlib"

def owner_to_addr(s):
    owner=s+"="
    hash=hashlib.sha256(base64.urlsafe_b64decode(owner)).hexdigest()
    bin=binascii.unhexlify(hash)
    addr=base64.urlsafe_b64encode(bin).decode()[:-1]
    return addr

def decode(b64_string):
    b64_string += "=" * ((4 - len(b64_string) % 4) % 4)
    return base64.urlsafe_b64decode(b64_string)

def create_collections():
    try:
        conn = pymongo.MongoClient(MONGO_STRING)
        db=conn[DATABASE]
        print("Connected successfully!")
    except Exception as ex:
        print(ex)
        print("Could not connect to MongoDB")
        exit()

    db.create_collection('blocks',
                     storageEngine={'wiredTiger':{'configString':'block_compressor='+MONGO_COMPRESSION}})

    db.create_collection('txs',
                     storageEngine={'wiredTiger':{'configString':'block_compressor='+MONGO_COMPRESSION}})

def create_indexes():
    try:
        conn = pymongo.MongoClient(MONGO_STRING)
        db=conn[DATABASE]
        print("Connected successfully!")
    except Exception as ex:
        print(ex)
        print("Could not connect to MongoDB")
        exit()

    #specify indexes for the DB collections
    #db.txs.createIndex( { "tags.name": 1, "tags.value": 1 } )
    block_indexes=["timestamp","height","indep_hash","reward_addr","block_size"]
    txs_indexes=["format","id","owner_address","tags","target","quantity","data_size","reward","height","timestamp"]

    for i in block_indexes:
        resp_idx = db.blocks.create_index([(i,1)])
        print ("Blocks index response:", i, resp_idx)
    for i in txs_indexes:
        resp_idx = db.txs.create_index([(i,1)])
        print ("Transactions index response:", i, resp_idx)


def interval_split(n1,n2,parts):
    r=[]
    size=round((n2-n1)/parts)
    for i in range(0,parts):
        if i==0: start=n1
        else: start=i*size+1+n1
        if i==(parts-1): end=n2
        else: end=i*size+size+n1
        r.append([start,end])
        #print(start,"->",end)
    return r

class Parser:
    def __init__(self,node,thread):
        self.peers=self.list_peers(node)
        self.wildfire={}
        self.total_requests=0
        self.thread_id=thread
        self.mongo=0

    def init_mongo(self):
        try:
            conn = pymongo.MongoClient(MONGO_STRING)
            self.db=conn[DATABASE]
            print(self.info(),"Connected successfully!")
        except Exception as ex:
            print(self.info(),ex)
            print(self.info(),"Could not connect to MongoDB")
            exit()
        self.mongo=1

    def info(self):
        return "THREAD "+str(self.thread_id)+":"

    def req(self,url,size=0):
        try:
            response=requests.get(url,timeout=NETWORK_TIMEOUT)
            content=response.content.decode("utf-8")
            if response.status_code!=200: return 0
            if size>0:
                if len(content)<size:
                    print(self.info(),"incomplete data?",url)
                    #return 0
            else: content=json.loads(content)
            return content
        except:
            print(self.info(),"Network Error")
            return 0


    def list_peers(self,node):
        response=self.req(node+"/peers")
        if response:
            #peers=json.loads(response)
            peers=response
            #do some cleanup
            for i in peers:
                if i.startswith("127.0"): peers.remove(i)
            return peers

        else:
            print("Cannot get data from", STARTING_NODE, "consider changing it")
            exit()

    def random_peer(self):
        #remove low wildfire score peers
        if self.total_requests>CLEANUP_INTERVAL:
            self.total_requests=0
            for e in self.peers:
                if (e in self.wildfire) and self.wildfire[e]<1 and len(self.peers)>MIN_PEERS:
                    #print(self.wildfire)
                    self.peers.remove(e)
                    print(self.info(),"removed bad peer",e)
        size=len(self.peers)
        id=random.randint(0,size-1)
        return self.peers[id]

    def get_block(self,height,peer=None):
        #print("THREAD",self.thread_id,self.total_requests)

        done=0
        while done==0:
            self.total_requests+=1
            peer=self.random_peer()
            print(self.info(),"getting block", height, "from", peer)
            result=self.req("http://"+peer+"/block/height/"+str(height))
            if result!=0:
                done=1
                self.wildfire[peer]=self.wildfire.get(peer, 0) + 1
                return result
            time.sleep(RETRY_DELAY)
            #self.wildfire[peer]=self.wildfire.get(peer, 0) - 1

    def get_tx(self,id,peer=None):
        done=0
        while done==0:
            self.total_requests+=1
            peer=self.random_peer()
            print(self.info(),"getting tx", id, "from",peer)
            result=self.req("http://"+peer+"/tx/"+id)
            if result!=0:
                done=1
                self.wildfire[peer]=self.wildfire.get(peer, 0) + 1
                return result
            time.sleep(RETRY_DELAY)
            #self.wildfire[peer]=self.wildfire.get(peer, 0) - 1

    def get_data(self,id,size,peer=None):
        done=0
        retries=0
        while done==0:
            retries+=1
            self.total_requests+=1
            peer=self.random_peer()
            print(self.info(),"getting tx data", id, "from",peer)
            result=self.req("http://"+peer+"/tx/"+id+"/data",size)
            if result!=0:
                done=1
                self.wildfire[peer]=self.wildfire.get(peer, 0) + 1
                return result
            if retries==5:
                print(self.info(),"returning empty data after 5 attempts")
                return ""
            time.sleep(RETRY_DELAY)

    def get_interval(self,n1,n2):
        if self.mongo==0: self.init_mongo()
        for i in range(n1,n2+1):
            block=self.get_block(i)
            self.db.blocks.insert_one(block)
            txs=block["txs"]
            for j in txs:
                tx=self.get_tx(j)
                if ("data_size" in tx) and int(tx["data_size"])>0:
                    data=self.get_data(j,int(tx["data_size"]))
                    print(self.info(),"received",len(data),"bytes")
                    tx["data"]=data

                tx["data"]=decode(tx["data"])
                #tx["signature"]=decode(tx["signature"])

                tx["height"]=block["height"]
                tx["timestamp"]=block["timestamp"]
                tx["owner_address"]=owner_to_addr(tx["owner"])
                new_tags=[]
                for k in tx["tags"]:
                    new_tags.append({"name": decode(k["name"]), "value": decode(k["value"])})
                tx["tags"]=new_tags

                self.db.txs.insert_one(tx)

    def smart_thread(self,start,end,step):
        remainder=start % step
        if start % 2 == 0:
            for j in range(start,end+1,step):
                #print(self.info(),j)
                self.get_interval(j,j)
        else:
            for j in range(start,end+1,step): new_end=j
            for j in range(new_end,start-1,-1*step):
                #print(self.info(),j)
                self.get_interval(j,j)

def multi(start,end):
#create object list
#    intervals=interval_split(490615,491615,THREADS)

    parsers=[None] * THREADS
    threads=[None] * THREADS
    for i in range(0,THREADS):
        new_start=start+i
        parsers[i]=Parser(STARTING_NODE,i+1)
        threads[i]=multiprocessing.Process(target=parsers[i].smart_thread, args=(new_start,end,THREADS))
        threads[i].start()
    try:
        print("waiting")
        for i in range(0,THREADS): threads[i].join()

    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        for i in range(0,THREADS):
            threads[i].terminate()
        for i in range(0,THREADS):
            threads[i].join()

def main():
    create_collections()
    create_indexes()
    t0=time.time()
    multi(START_BLOCK,END_BLOCK)
    print(round(time.time()-t0),"sec for",END_BLOCK-START_BLOCK,"blocks")

if __name__ == "__main__":
    main()

