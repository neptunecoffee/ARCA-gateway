# Gateway HTTP API
#### Retrieve a JSON transaction record via the specified ID.
   GET ```/tx/[transaction_id]```
   
#### Retrieve transaction data.
   GET ```/tx/[transaction_id]/data```
   
#### Retrieve block via ID.
   GET ```/block/hash/[block_id]```
   
#### Retrieve block via height.
   GET ```/block/height/[block_height]```
   
#### Retrieve transaction base64 decoded data with self specified content type headers.
   GET ```/[transaction_id]```
   
#### Retrieve a ZIP transaction record via the specified ID. 
   GET ```/ziptx/[transaction_id]```
   
#### Retrieve ZIP transaction data via the specified ID.
   GET ```/ziptx/[transaction_id]/data```
   
#### Retrieve ZIP block via ID.
   GET ```/zipblock/hash/[block_id]```

#### Retrieve ZIP block via height.
   GET ```/zipblock/height/[block_height]```
   
For the ZIP endpoints, data can be decompressed with:

``` zlib.decompress(response.content).decode("UTF-8")``` (Python3)
