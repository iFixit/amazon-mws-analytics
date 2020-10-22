"""Support making requests to MWS and massaging the returned data."""

import sys
import time

import iso8601


def flatten(tree):
    """Convert tree, replacing {"value": x} nodes with x and converting values
    to specific types based on the key.
    """
    if isinstance(tree, list):
        return list(map(flatten, tree))

    # If the tree is a leaf, simply return the value.
    if list(tree.keys()) == ["value"]:
        return tree["value"]

    if "value" in tree:
        del tree["value"]

    # If the tree has children, recurse.
    flattened = {}
    for key in tree.keys():
        flattened[key] = convert_types(key, flatten(tree[key]))

    return flattened


def convert_types(key, value):
    """Convert value to a known type based on key."""
    boolean_keys = [
        "IsReplacementOrder",
        "IsBusinessOrder",
        "IsPremiumOrder",
        "IsPrime",
        "IsGift",
    ]

    date_keys = ["LatestShipDate", "PurchaseDate", "LastUpdateDate", "EarliestShipDate"]

    int_keys = [
        "NumberOfItemsShipped",
        "NumberOfItemsUnshipped",
        "QuantityOrdered",
        "NumberOfItems",
        "QuantityShipped",
    ]

    float_keys = ["Amount"]

    if key in boolean_keys:
        return key == "true"
    if key in date_keys:
        return iso8601.parse_date(value)
    if key in int_keys:
        return int(value)
    if key in float_keys:
        return float(value)
    return value


def make_ratelimit_aware(error_cls, make_request, wait_seconds):
    """Return a function that wraps make_request, catching error_cls and
    retrying the request one more time after waiting wait_seconds.

    error_cls -- a type of Exception to catch
    make_request -- a function that makes a request to MWS
    wait_seconds -- an int or float: fractional seconds to wait before retry
    """

    def ratelimit_runner(*args, **kwargs):
        try:
            return make_request(*args, **kwargs)
        except error_cls as err:
            print(f"error: {err}", file=sys.stderr)
            time.sleep(wait_seconds)
            return make_request(*args, **kwargs)

    return ratelimit_runner
