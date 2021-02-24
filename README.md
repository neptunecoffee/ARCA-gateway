# ARCA-gateway
## Installaton and requirements
+ Tested on Ubuntu 18.04
+ MongoDB 4.2
```
   $ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 4B7C549A058F8B6B
   $ echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb.list
   $ sudo apt update
   $ sudo apt install mongodb-org=4.2.8 mongodb-org-server=4.2.8 mongodb-org-shell=4.2.8 mongodb-org-mongos=4.2.8 mongodb-org-tools=4.2.8
```
+ Python3
```
   $ apt-get install python3 
   $ apt-get install python3-requests
 ```
+ Flask 1.1
```
   $ pip3 install Flask
```
+ Waitress 1.4
```
   $ pip3 install waitress
```
+ Graphene 2.1.8
```
   $ pip3 install "graphene>=2.0"
```
+ Flask-Graphql 2.0.1
```
   $ pip3 install flask_graphql
```

1. Start Mongo
2. Edit remote_pop.py (threads, database name, etc)
3. Run ./remote_pop.py 
