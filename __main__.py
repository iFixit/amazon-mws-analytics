import os
from datetime import datetime, timedelta

from mws import mws
from functools import partial
from pymongo import MongoClient, ReplaceOne

from .orders import get_order_items, get_all_orders
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
orders = get_all_orders(
    retry_minute_after_ratelimit(get_us_orders_from_yesterday),
    retry_minute_after_ratelimit(orders_api.list_orders_by_next_token))

# Create function to get order_items for each order
add_order_items = partial(
    get_order_items,
    retry_minute_after_ratelimit(orders_api.list_order_items),
    retry_minute_after_ratelimit(orders_api.list_order_items_by_next_token))

orders = map(add_order_items, orders)

UpsertOne = partial(ReplaceOne, upsert=True)
bulk_upserts = map(lambda order: UpsertOne({"_id": order['_id']}, order), orders)

mongo = MongoClient(os.environ['MONGODB_URI'])
mongo.warehouse.amazon_orders.bulk_write(list(bulk_upserts))
