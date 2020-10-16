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

import iso8601
from mws import mws
from pymongo import MongoClient

from .orders import generate_orders, set_order_items
from .utils import make_ratelimit_aware

orders_api = mws.Orders(
    os.environ["AWS_ACCESS_KEY"],
    os.environ["MWS_SECRET_KEY"],
    os.environ["MWS_SELLERID"],
    region=os.environ["REGION"],
)

MARKETPLACEIDS = os.environ["MARKETPLACEIDS"].split(",")

START_DATE = None
END_DATE = None
if "START_DATE" in os.environ:
    START_DATE = iso8601.parse_date(os.environ["START_DATE"]).isoformat()
    if "END_DATE" in os.environ:
        END_DATE = iso8601.parse_date(os.environ["END_DATE"]).isoformat()
else:
    DAYS_AGO = 1 if "DAYS_AGO" not in os.environ else int(os.environ["DAYS_AGO"])
    START_DATE = datetime.now() - timedelta(days=DAYS_AGO).isoformat()

display_end_date = END_DATE if END_DATE is not None else "now"
print(f"Fetching orders between {START_DATE} and {display_end_date}")

get_orders_from_start_date = partial(
    orders_api.list_orders,
    marketplaceids=MARKETPLACEIDS,
    lastupdatedafter=START_DATE,
    lastupdatedbefore=END_DATE,
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

# ListOrderItems has max quota 30 and restore rate 1 per 2s. We aim to only
# very slowly wear down the quota and, in the event that we hit the limit, we
# wait 60s to restore the full pool.
set_order_items_with_retry = partial(
    set_order_items,
    retry_after_error(orders_api.list_order_items, 60),
    retry_after_error(lambda t: orders_api.list_order_items(next_token=t), 60),
)

orders_with_items = []
for i, order in enumerate(orders_itr):
    if i > 0:
        time.sleep(1.75)
    order["_id"] = order["AmazonOrderId"]
    set_order_items_with_retry(order)
    orders_with_items.append(order)

mongo = MongoClient(os.environ["MONGODB_URI"])
upsert_order = partial(mongo.warehouse.amazon_orders.replace_one, upsert=True)
for order in orders_with_items:
    print(f"Upserting {order['_id']}...", end=" ")
    upsert_order({"_id": order["_id"]}, order)
    print("done")
