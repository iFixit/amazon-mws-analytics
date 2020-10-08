# This file is for shared functionality between Amazon grabbing stuff
import iso8601
import sys
import time


def flatten(tree):
    if type(tree) is list:
        return list(map(flatten, tree))

    # If the tree is a leaf, simply return the value.
    if list(tree.keys()) == ["value"]:
        return tree["value"]

    if "value" in tree:
        del tree["value"]
    flattened = {}

    # If the tree has children, recurse.
    for key in tree.keys():
        flattened[key] = convert_types(key, flatten(tree[key]))

    return flattened


def convert_types(key, value):
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


def make_ratelimit_aware(error, wait_seconds, fn):
    def ratelimit_runner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except error:
            print("ratelimited", file=sys.stderr)
            time.sleep(wait_seconds)
            return fn(*args, **kwargs)

    return ratelimit_runner
