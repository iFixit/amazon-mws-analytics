"""Tests for orders"""

from dataclasses import dataclass

from .orders import generate_orders


@dataclass
class OrdersGetter:
    """Fake class to represent results of running an order_getter"""

    parsed: list


def get_order_getter(orders):
    """Get first-batch order getter"""
    parsed = {"Orders": orders, "NextToken": {"value": "nextTok"}}
    return lambda: OrdersGetter(parsed)


def get_orders_next_getter(orders):
    """Get rest-batch order getter"""
    parsed = {"Orders": orders}
    return lambda token: OrdersGetter(parsed)


def test_generate_orders_with_empty_next_page():
    """Test that a batch of orders which includes a NextToken but has no
    orders on the next page doesn't crash the code.

    """
    orders_getter = get_order_getter({"Order": [{}, {}]})
    # Results from next batch of orders don't even have an `Order` key:
    orders_next_getter = get_orders_next_getter(orders={})
    generator = generate_orders(orders_getter, orders_next_getter)
    orders = list(generator)
    print(orders)
