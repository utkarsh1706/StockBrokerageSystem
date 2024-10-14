from schema import Trade, Orders
import json
import time
from mongoengine import connect, ConnectionError, DoesNotExist, ValidationError
import redis
from dotenv import load_dotenv
import os
from constants import *
from schema import OrderSide, OrderStatus

load_dotenv()

mongoURI = os.getenv("mongoURI")
redisPassword = os.getenv("redisPassword")
redisHost = os.getenv("redisHost")
redisPort = os.getenv("redisPort")

try:
    connect(db="StockBrokerSystem", host=mongoURI)
except ConnectionError as e:
    print(f"Error connecting to the database: {e}")

try:
    redisClient = redis.Redis(host=redisHost, port=redisPort, password=redisPassword)
    redisClient.ping()
    print("Connected to Redis")
except redis.ConnectionError as e:
    print("Redis not connected due to ", e)

def updateTrades():
    try:
        tradeDataList = redisClient.lrange("tradeData", 0, -1)
        
        for tradeData in tradeDataList:
            try:
                trade = json.loads(tradeData)
                
                if not Trade.objects(unique_id=trade['unique_id']):
                    newTrade = Trade(
                        unique_id=trade['unique_id'],
                        execution_timestamp=trade['execution_timestamp'],
                        price=trade['price'],
                        qty=trade['qty'],
                        bid_order_id=trade['bid_order_id'],
                        ask_order_id=trade['ask_order_id']
                    )
                    newTrade.save()
                    print(f"Saved new trade: {newTrade.unique_id}")
            except json.JSONDecodeError as e:
                print(f"Error decoding trade data: {e}")
            except ValidationError as e:
                print(f"Error saving trade: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    except Exception as e:
        print(f"Error fetching trade data from Redis: {e}")

def updateOrders():
    try:
        keys = redisClient.keys('order:*')
        
        for orderKey in keys:
            try:
                orderData = redisClient.hgetall(orderKey)
                if orderData:
                    orderData = {k.decode('utf-8'): v.decode('utf-8') for k, v in orderData.items()}
                    oid = orderData['oid']
                    price = float(orderData['price'])
                    quantity = float(orderData['quantity'])
                    filledQuantity = float(orderData['filledQuantity'])
                    averagePrice = float(orderData['averagePrice'])
                    placedTimestamp = int(orderData['placedTimestamp'])
                    lastUpdatesTimestamp = int(orderData['lastUpdatesTimestamp'])
                    sideStr = orderData['side'] 
                    statusStr = orderData['status'].replace(' ', '_')
                    status = OrderStatus[statusStr]
                    side = OrderSide[sideStr]
                    clientOrderId = orderData['clientOrderId']
                    
                    existingOrder = Orders.objects(oid=oid).first()
                    
                    if existingOrder:
                        existingOrder.update(
                            price=price,
                            quantity=quantity,
                            filledQuantity=filledQuantity,
                            averagePrice=averagePrice,
                            lastUpdatesTimestamp=lastUpdatesTimestamp,
                            status=status,
                            side=side
                        )
                        print(f"Updated order: {oid}")
                    else:
                        newOrder = Orders(
                            oid=oid,
                            price=price,
                            quantity=quantity,
                            filledQuantity=filledQuantity,
                            averagePrice=averagePrice,
                            placedTimestamp=placedTimestamp,
                            lastUpdatesTimestamp=lastUpdatesTimestamp,
                            status=status,
                            side=side,
                            clientOrderId=clientOrderId
                        )
                        newOrder.save()
                        print(f"Saved new order: {newOrder.oid}")

            except KeyError as e:
                print(f"Missing key in order data: {e}")
            except ValueError as e:
                print(f"Error converting data type: {e}")
            except ValidationError as e:
                print(f"Error saving order: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing order {orderKey}: {e}")
    
    except Exception as e:
        print(f"Error fetching order keys from Redis: {e}")

def main():
    while True:
        print("Updating MongoDB")
        updateTrades()
        updateOrders()
        time.sleep(30)

if __name__ == "__main__":
    main()
