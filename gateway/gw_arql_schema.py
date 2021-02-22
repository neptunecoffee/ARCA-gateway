#!/usr/bin/python3
import graphene
from gw_arql_data import get_transaction,get_transactions


class TagInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    value = graphene.String(required=True)


class Tag(graphene.ObjectType):
    name = graphene.String(required=True)
    value = graphene.String(required=True)


class Transaction(graphene.ObjectType):
    id = graphene.String(required=True)
    tags = graphene.List(Tag)
    height = graphene.Int(required=True)
    timestamp = graphene.Int(required=True)
    tag_value = graphene.String(tag_name=graphene.String(), required=True)
    """
    Which transaction this tx refers to, by keeping its ID in the value of "byOwnTag" tag
    """
    linked_to_transaction = graphene.Field(lambda: Transaction, by_own_tag=graphene.String(required=True))
    linked_from_transactions = graphene.List(lambda: Transaction, by_foreign_tag = graphene.String(required=True),
                                                                  to = graphene.String(),
                                                                  tags = graphene.List(TagInput),
                                                                  args={'from': graphene.String()}
                               )
    count_linked_from_transactions = graphene.Int(by_foreign_tag = graphene.String(required=True),
                                                  args={'from': graphene.String()},
                                                  to = graphene.String(),
                                                  tags = graphene.List(TagInput),
                                                  required=True
                                     )

    def resolve_tag_value(parent, info, tag_name):
        for tag in parent.tags:
            if tag["name"] == tag_name:
                return tag["value"]

    def resolve_linked_to_transaction(parent, info, by_own_tag):
        for tag in parent.tags:
            if tag["name"] == by_own_tag:
                linked_tx_id = tag["value"]
                linked_tx = get_transaction(linked_tx_id)
                if linked_tx is not None:
                    return Transaction(id = linked_tx_id,
                                       tags = linked_tx["tags"]
                    )
                else:
                    return None

    def resolve_linked_from_transactions(parent, info, by_foreign_tag, **kwargs):
        txs = get_transactions(**kwargs)
        linking_txs = []
        for tx in txs:
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
                            if tag_name == by_foreign_tag:
                                if tag_value == parent.id:
                                    linking_txs.append(Transaction(id = tx["id"], tags = tags))
                        else:
                            raise Exception("Malformed tag in tag. 'Name' with no 'value' pair.")
                    else:
                        raise Exception("Malformed tag in tags: no 'name' attribute.")
        return linking_txs

    def resolve_count_linked_from_transactions(parent, info, by_foreign_tag, **kwargs):
        txs = get_transactions(**kwargs)
        count = 0
        for tx in txs:
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
                            if tag_name == by_foreign_tag:
                                if tag_value == parent.id:
                                    count += 1
                        else:
                            raise Exception("Malformed tag in tags. 'name' with no 'value' pair.")
                    else:
                        raise Exception("Malformed tag in tags: no 'name' attribute.")
        return count

class Query(graphene.ObjectType):
    transaction = graphene.Field(Transaction, id=graphene.String())
    transactions = graphene.List(Transaction, args={'from': graphene.String()}, to=graphene.String(), tags=graphene.List(TagInput))
    count_transactions = graphene.Int(required=True, args={'from': graphene.String()}, to=graphene.String(), tags=graphene.List(TagInput))

    def resolve_transaction(parent, info, id):
        tx = get_transaction(id)
        if tx is not None:
            if "tags" not in tx:
                tx["tags"] = None
            if "height" not in tx:
                tx["height"] = None
            if "timestamp" not in tx:
                tx["timestamp"] = None
            return Transaction(id = id,
                               tags = tx["tags"],
                               height = tx["height"],
                               timestamp = tx["timestamp"]
            )
        else:
           return None

    def resolve_transactions(parent, info, **kwargs):
        txs = get_transactions(**kwargs)
        transactions = []
        if txs is not None:
            for tx in txs:
                if "height" not in tx:
                    tx["height"] = None
                if "timestamp" not in tx:
                    tx["timestamp"] = None
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
                    transactions.append(Transaction(id = tx["id"], tags = tags, height = tx["height"], timestamp = tx["timestamp"]))
                else:
                    transactions.append(Transaction(id = tx["id"], height = tx["height"], timestamp = tx["timestamp"]))
        return transactions

    def resolve_count_transactions(parent, info, **kwargs):
        txs = get_transactions(**kwargs)
        count_txs = 0
        for tx in txs:
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
            count_txs += 1
        return count_txs

ar_schema = graphene.Schema(query=Query)
