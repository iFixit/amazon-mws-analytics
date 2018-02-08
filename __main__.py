import os
from datetime import datetime, timedelta

from mws import mws
from functools import partial
from pymongo import MongoClient, ReplaceOne

from .orders import get_order_items, orders_generator, set_document_id
from .utils import make_ratelimit_aware

marketplaceids = os.environ['MARKETPLACEIDS'].split(",")
days_ago = 1 if 'DAYS_AGO' not in os.environ else int(os.environ['DAYS_AGO'])
orders_api = mws.Orders(os.environ['AWS_ACCESS_KEY'],
                        os.environ['MWS_SECRET_KEY'],
                        os.environ['MWS_SELLERID'],
                        region=os.environ['REGION'])

start_date = datetime.now() - timedelta(days=days_ago)
get_us_orders_from_start_date = partial(orders_api.list_orders,
                                    marketplaceids=marketplaceids,
                                    lastupdatedafter=start_date.isoformat())
retry_minute_after_ratelimit = partial(make_ratelimit_aware, mws.MWSError, 60)

# Get all orders from Amazon
orders = orders_generator(
    retry_minute_after_ratelimit(get_us_orders_from_start_date),
    retry_minute_after_ratelimit(orders_api.list_orders_by_next_token))

# Create function to get order_items for each order
add_order_items = partial(
    get_order_items,
    retry_minute_after_ratelimit(orders_api.list_order_items),
    retry_minute_after_ratelimit(orders_api.list_order_items_by_next_token))

orders = map(set_document_id, map(add_order_items, orders))

mongo = MongoClient(os.environ['MONGODB_URI'])
upsert_order = partial(mongo.warehouse.amazon_orders.replace_one, upsert=True)
for order in orders:
    upsert_order({"_id": order['_id']}, order)
