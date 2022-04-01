"""Fetch and flatten orders and their items."""

from .utils import flatten


def generate_orders(orders_getter, orders_next_getter):
    """Return a stream of orders."""
    print("Listing orders...", end=" ")
    orders_res = orders_getter().parsed

    if "Order" not in orders_res["Orders"]:
        print("no orders")
        return

    flattened_res = _flatten_orders(orders_res)
    orders = flattened_res["Orders"]["Order"]
    print(f"{len(orders)} orders")
    yield from orders

    while "NextToken" in flattened_res:
        print("Listing more orders by NextToken...", end=" ")
        orders_res = orders_next_getter(flattened_res["NextToken"]).parsed

        if "Order" not in orders_res["Orders"]:
            print("no orders")
            return

        flattened_res = _flatten_orders(orders_res)
        orders = flattened_res["Orders"]["Order"]
        print(f"{len(orders)} orders")
        yield from orders


def _flatten_orders(orders_res):
    orders = orders_res["Orders"]["Order"]
    # If there's only one order, it is serialized as a dict.
    if not isinstance(orders, list):
        orders = [orders]
    orders_res["Orders"]["Order"] = orders
    return flatten(orders_res)


def set_order_items(item_getter, item_next_getter, order):
    """Set the "OrderItems" key of an Order dict with the items associated with
    that order.
    """
    orderid = order["AmazonOrderId"]
    last_updated = order["LastUpdateDate"].isoformat(timespec="seconds")
    print(f"Listing items for order {orderid} ({last_updated})...", end=" ")
    items_res = item_getter(order["AmazonOrderId"]).parsed
    flattened_res = _flatten_items(items_res)
    items = flattened_res["OrderItems"]["OrderItem"]
    print(f"{len(items)} items")
    order["OrderItems"] = items

    while "NextToken" in flattened_res:
        print("Listing more items by NextToken...", end=" ")
        items_res = item_next_getter(flattened_res["NextToken"]).parsed
        flattened_res = _flatten_items(items_res)
        items = flattened_res["OrderItems"]["OrderItem"]
        print(f"{len(items)} items")
        order["OrderItems"].extend(items)


def _flatten_items(items_res):
    items = items_res["OrderItems"]["OrderItem"]
    # If there's only one item, it is serialized as a dict.
    if not isinstance(items, list):
        items = [items]
    items_res["OrderItems"]["OrderItem"] = items
    return flatten(items_res)
