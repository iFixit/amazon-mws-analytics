"""Fetch orders and their items from the Amazon MWS API for MARKETPLACEIDS,
starting from now and going back DAYS_AGO days.

All arguments are specified as environment variables. MARKETPLACEIDS must be
present and is a comma-separated list of Amazon marketplace identifiers (e.g.,
A2EUQ1WTGCTBG2). DAYS_AGO is an integer number of days and defaults to 1 if not
present.
"""

import os
import time
from datetime import datetime, timedelta
from functools import partial

from mws import mws
from pymongo import MongoClient

from .orders import set_order_items, generate_orders
from .utils import make_ratelimit_aware

MARKETPLACEIDS = os.environ["MARKETPLACEIDS"].split(",")
DAYS_AGO = 1 if "DAYS_AGO" not in os.environ else int(os.environ["DAYS_AGO"])

orders_api = mws.Orders(
    os.environ["AWS_ACCESS_KEY"],
    os.environ["MWS_SECRET_KEY"],
    os.environ["MWS_SELLERID"],
    region=os.environ["REGION"],
)

start_date = datetime.now() - timedelta(days=DAYS_AGO)
get_orders_from_start_date = partial(
    orders_api.list_orders,
    marketplaceids=MARKETPLACEIDS,
    lastupdatedafter=start_date.isoformat(),
)

retry_after_error = partial(make_ratelimit_aware, mws.MWSError)

# ListOrders has max quota 6 and restore rate 1 per 60s. We spend most of our
# time fetching items, so we can rely on waiting for those to restore the pool.
# In the event that we hit the limit, we wait 180s to restore half the pool
# (but this is quite unlikely, and should really only happen if some other task
# is hitting the API at the same time).
orders_itr = generate_orders(
    retry_after_error(get_orders_from_start_date, 180),
    retry_after_error(orders_api.list_orders_by_next_token, 180),
)

# ListOrderItems has max quota 30 and restore rate 1 per 2s. We aim to slowly
# wear down the quota and, in the event that we hit the limit, we wait 60s to
# restore the full pool.
set_order_items_with_retry = partial(
    set_order_items,
    retry_after_error(orders_api.list_order_items, 60),
    retry_after_error(orders_api.list_order_items_by_next_token, 60),
)

orders_with_items = []
for i, order in enumerate(orders_itr):
    if i > 0:
        time.sleep(1.5)
    order["_id"] = order["AmazonOrderId"]
    set_order_items_with_retry(order)
    orders_with_items.append(order)

mongo = MongoClient(os.environ["MONGODB_URI"])
upsert_order = partial(mongo.warehouse.amazon_orders.replace_one, upsert=True)
for order in orders_with_items:
    print(f"Upserting {order['_id']}...", end=" ")
    upsert_order({"_id": order["_id"]}, order)
    print("done")
