# This is for orders functions
from .utils import flatten

def orders_generator(orders_getter, orders_next_getter):
    """Returns a generator for all orders"""
    orders_res = orders_getter()
    flattened_res = flatten(orders_res.parsed)

    if 'Order' not in flattened_res['Orders']:
        return

    yield from flattened_res['Orders']['Order']

    while 'NextToken' in flattened_res:
        orders_res = orders_next_getter(flattened_res['NextToken'])
        flattened_res = flatten(orders_res.parsed)

        yield from flattened_res['Orders']['Order']

def get_order_items(item_getter, item_next_getter, order):
    items = item_getter(order['AmazonOrderId'])
    # TODO: Need to implement nextToken for orders with a shit ton of items

    clean_items = lambda item: flatten(process_order_items(item))
    order['OrderItems'] = clean_items(items)
    return order

def process_order_items(items):
    items = items.parsed['OrderItems']['OrderItem']

    # If there's only one item is serialized as a dict.
    if type(items) is not list:
        items = [items]

    return list(map(lambda item: item['OrderItem'], items))

def set_document_id(order):
    order['_id'] = order['AmazonOrderId']
    return order
