import os
from datetime import datetime, timedelta

from mws import mws
from functools import partial
from pymongo import MongoClient, ReplaceOne

from .orders import get_order_items, get_all_orders
from .utils import make_ratelimit_aware

orders_api = mws.Orders(os.environ['US_AWS_ACCESS_KEY'],
                        os.environ['US_MWS_SECRET_KEY'],
                        os.environ['US_MWS_SELLERID'],
                        region="US")

yesterday = datetime.now() - timedelta(days=1)

marketplace_usa = 'ATVPDKIKX0DER'
get_us_orders_from_yesterday = partial(orders_api.list_orders,
                                    marketplaceids=[marketplace_usa],
                                    lastupdatedafter=str(yesterday))
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
