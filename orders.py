# This is for orders functions
from .utils import flatten

# TODO: Make sure to set _id to AmazonOrderId
def get_all_orders(orders_getter, orders_next_getter):
    def get_next_orders(orders_res):
        """Given an Orders Resource, paginate through all Orders."""
        flattened_res = flatten(orders_res.parsed)
        orders = flattened_res['Orders']['Order']

        if 'NextToken' not in flattened_res:
            return orders

        next_token = flattened_res['NextToken']
        next_orders = orders_next_getter(next_token)

        return orders + get_next_orders(next_orders)

    return list(map(set_document_id, get_next_orders(orders_getter())))

def get_order_items(item_getter, item_next_getter, order):
    items = item_getter(order['AmazonOrderId'])
    # TODO: Need to implement nextToken for orders with a shit ton of items

    clean_items = lambda item: flatten(process_order_items(item))
    order['OrderItems'] = clean_items(items)
    return order

def process_order_items(items):
    items = items.parsed['OrderItems']

    # If there's only one item is serialized as a dict.
    if type(items) is not list:
        items = [items]

    return list(map(lambda item: item['OrderItem'], items))

def set_document_id(order):
    order['_id'] = order['AmazonOrderId']
    return order
