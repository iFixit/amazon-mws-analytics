from .utils import flatten


def orders_generator(orders_getter, orders_next_getter):
    """Returns a generator for all orders"""
    print("Listing orders...", end=" ")
    orders_res = orders_getter().parsed

    if "Order" not in orders_res["Orders"]:
        print("no orders")
        return

    flattened_res = flatten_orders(orders_res)
    orders = flattened_res["Orders"]["Order"]
    print(f"{len(orders)} orders")
    yield from orders

    while "NextToken" in flattened_res:
        print("Listing more orders by NextToken...", end=" ")
        orders_res = orders_next_getter(flattened_res["NextToken"]).parsed
        flattened_res = flatten_orders(orders_res)
        orders = flattened_res["Orders"]["Order"]
        print(f"{len(orders)} orders")
        yield from orders


def flatten_orders(orders_res):
    orders = orders_res["Orders"]["Order"]
    # If there's only one order, it is serialized as a dict.
    if not isinstance(orders, list):
        orders = [orders]
    orders_res["Orders"]["Order"] = orders
    return flatten(orders_res)


def set_order_items(item_getter, item_next_getter, order):
    print(f"Listing items for order {order['AmazonOrderId']}...", end=" ")
    items_res = item_getter(order["AmazonOrderId"]).parsed
    # TODO: Need to implement nextToken for orders with a shit ton of items
    flattened_items = flatten_items(items_res)
    print(f"{len(flattened_items)} items")
    order["OrderItems"] = flattened_items


def flatten_items(items_res):
    items = items_res["OrderItems"]["OrderItem"]
    # If there's only one item, it is serialized as a dict.
    if not isinstance(items, list):
        items = [items]
    return flatten(items)


def set_document_id(order):
    order["_id"] = order["AmazonOrderId"]
