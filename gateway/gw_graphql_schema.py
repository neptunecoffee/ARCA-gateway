import graphene
from graphene import relay, Enum
from gw_graphql_data import get_transaction, get_transactions, get_block, get_blocks

class SortOrder(Enum):
    HEIGHT_ASC = 1
    HEIGHT_DESC = -1


class TagOperator(Enum):
    EQ = "$in"
    NEQ = "$nin"


class TagFilter(graphene.InputObjectType):
    name = graphene.String(required=True)
    values = graphene.List(graphene.NonNull(graphene.String), required=True)
    op = graphene.Field(TagOperator, default_value = '$in')


class BlockFilter(graphene.InputObjectType):
    '''Find transactions within a block height range.'''
    min = graphene.Int(description='The minimum block height to filter from.')
    max = graphene.Int(description='The maximum block height to filter from.')


class Tag(graphene.ObjectType):
    '''A single tag'''
    name = graphene.String(required=True)
    value = graphene.String(required=True)


class Owner(graphene.ObjectType):
    '''The owner of the transaction'''
    address = graphene.String(required=True)
    key = graphene.String(required=True)


class Amount(graphene.ObjectType):
    '''Coin amount, e.g. the fee or the quantity'''
    winston = graphene.String(required=True)
    ar = graphene.String(required=True)
    def resolve_ar(self, info):
        ar = int(self.winston) / 1e12
        return f"{ar:.12f}"


class Block(graphene.ObjectType):
    id = graphene.String(required=True)
    timestamp = graphene.Int(required=True)
    height = graphene.Int(required=True)
    previous = graphene.String(required=True, description = "The ID of the previous block")

    def resolve_id(parent, info):
        if parent.height:
            block = get_block(height=parent.height)
            if "indep_hash" in block:
                return block["indep_hash"]
        return None

    def resolve_timestamp(parent, info):
        if parent.height:
            block = get_block(height=parent.height)
            if "timestamp" in block:
                return block["timestamp"]
        return None

    def resolve_previous(parent, info):
        if parent.height:
            block = get_block(height=parent.height)
            if "previous" in block:
                 return block["previous"]
        return None


class Transaction(graphene.ObjectType):
    '''A transaction....'''

    class Meta:
        interfaces = [relay.Node]

    id = graphene.ID(required=True)
    anchor = graphene.String(required=True)
    signature = graphene.String(required=True)
    recipient = graphene.String(required=True)
    owner = graphene.Field(Owner, required=True)
    fee = graphene.Field(Amount, required=True)
    quantity = graphene.Field(Amount, required=True)
    #data = graphene.Field(MetaData, required = True)
    tags = graphene.List(Tag)
    block = graphene.Field(Block)
    #parent = graphene.Field(Parent)

    @classmethod
    def get_node(cls, info, id):
         return get_transaction(id)

    def resolve_tag_value(parent, info, tag_name):
        for tag in parent.tags:
            if tag["name"] == tag_name:
                return tag["value"]


class TransactionConnection(relay.Connection):

    class Meta:
        node = Transaction


class BlockConnection(relay.Connection):

    class Meta:
        node = Block


class Query(graphene.ObjectType):
    transaction = graphene.Field(Transaction, id=graphene.String())
    transactions = relay.ConnectionField(
             TransactionConnection, description="Get a paginated set of matching transactions using filters.",
             owners=graphene.List(graphene.String, description="Find transactions from a list of owner wallet addresses, or wallet owner public keys."),
             recipients=graphene.List(graphene.String, description="Find transactions from a list of recipient wallet addresses."),
             tags=graphene.List(graphene.NonNull(TagFilter),description="Find transactions using filters."),
             block=BlockFilter(description="Find transactions within a given block height range."),
             ids=graphene.List(graphene.NonNull(graphene.String), description="Find transactions from a list of ids."),
             sort=SortOrder(default_value=-1, description="Optionally specify the result sort order."),
             first = graphene.Argument(graphene.Int, default_value = 10, description="Result page size (max: 100)")
    )
    block = graphene.Field(Block, id=graphene.String(), description = "Retrieve a Block by its ID")
    blocks = relay.ConnectionField(
           BlockConnection, description = "...", ids=graphene.List(graphene.NonNull(graphene.String)), height=BlockFilter(),
            sort=SortOrder(default_value=-1), first = graphene.Argument(graphene.Int, default_value = 10)
    )

    def resolve_transaction(parent, info, id):
        tx = get_transaction(id)
        if tx is not None:
            if "last_tx" not in tx:
                tx["last_tx"] = None
            if "signature" not in tx:
                tx["signature"] = None
            if "recipient" not in tx:
                tx["recipient"] = None
            if "tags" not in tx:
                tx["tags"] = None
            if "height" not in tx:
                tx["height"] = None
            if "timestamp" not in tx:
                tx["timestamp"] = None
            if "target" not in tx:
                tx["target"] = None
            if "owner_address" not in tx:
                tx["owner_address"] = None
            if "owner" not in tx:
                tx["owner"] = None
            if "reward" not in tx:
                tx["reward"] = None
            if "quantity" not in tx:
                tx["quantity"] = None
            return Transaction(id = id,
                               tags = tx["tags"],
                               anchor = tx["last_tx"],
                               signature = tx["signature"],
                               recipient = tx["target"],
                               owner = Owner(address = tx["owner_address"], key = tx["owner"]),
                               fee = Amount(winston = tx["reward"]),
                               quantity = Amount(winston = tx["quantity"]),
                               block = Block(height = tx["height"])
            )
        else:
           return None

    def resolve_transactions(parent, info, **kwargs):
        txs = get_transactions(**kwargs)
        transactions = []
        for tx in txs:
            if "signature" not in tx:
                tx["signature"] = None 
            if "last_tx" not in tx:
                tx["last_tx"] = None
            if "target" not in tx:
                tx["target"] = None
            if "tags" in tx:
                tags = tx["tags"]
                for tag in tags:
                    if "name" in tag:
                        if hasattr(tag["name"],"decode"):
                            tag_name = tag["name"].decode("UTF-8","backslashreplace")
                        else:
                            tag_name = tag["name"]
                        tag["name"] = tag_name
                        if "value" in tag:
                            if hasattr(tag["value"],"decode"):
                                tag_value = tag["value"].decode("UTF-8","backslashreplace")
                            else:
                                tag_value = tag["value"]
                            tag["value"] = tag_value
                        else:
                            raise Exception("Malformed tag in tag. 'name' with no 'value' pair.")
                    else:
                        raise Exception("Malformed tag in tags: no 'name' attribute.")
                transactions.append(Transaction(id = tx["id"], anchor = tx["last_tx"], signature = tx["signature"], recipient = tx["target"], 
                                        owner = Owner(address = tx["owner_address"], key = tx["owner"]),
                                        fee = Amount(winston = tx["reward"]),
                                        quantity = Amount(winston = tx["quantity"]),
                                        block = Block(height = tx["height"]),
                                        tags = tags
                ))
            else:
                transactions.append(Transaction(id = tx["id"]))
        return transactions

    def resolve_block(parent, info, **kwargs):
        block = get_block(**kwargs)
        if block:
            if "id" not in block:
                block["id"] = None
            if "height" not in block:
                block["height"] = None
            if "timestamp" not in block:
                block["timestamp"] = None
            if "previous" not in block:
                block["previous"] = None
            return Block(id = block["id"],
                     height = block["height"],
                     timestamp = block["timestamp"],
                     previous = block["previous"]
                   )
        else:
            return None

    def resolve_blocks(parent, info, **kwargs):
        bcks = get_blocks(**kwargs)
        blocks = []
        for b in bcks:
            if "indep_hash" not in b:
                b["indep_hash"] = None
            if "height" not in b: 
                b["height"] = None
            if "timestamp" not in b:
                b["timestamp"] = None
            blocks.append(Block(id = b["indep_hash"], height = b["height"], timestamp = b["timestamp"]))
        return blocks

g_schema = graphene.Schema(query=Query)
