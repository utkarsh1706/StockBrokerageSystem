from schema import Trade, Orders
import json
import time
from mongoengine import connect
import redis
from dotenv import load_dotenv
import os
from constants import *
from schema import OrderSide, OrderStatus

load_dotenv()

mongoURI = os.getenv("mongoURI")

connect(db="StockBrokerSystem", host = mongoURI)

redisClient = redis.Redis(host=redisHost, port=redisPort, password=redisPassword)

def updateTrades():

    tradeDataList = redisClient.lrange("tradeData", 0, -1)
    
    for tradeData in tradeDataList:
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

def updateOrders():
    keys = redisClient.keys('order:*')
    
    for orderKey in keys:
        orderData = redisClient.hgetall(orderKey)
        if orderData:
            # Decode both keys and values
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
            
            # Check if the order exists in MongoDB
            existingOrder = Orders.objects(oid=oid).first()
            
            if existingOrder:
                # Update existing order
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
                # Create a new order if it doesn't exist
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

def main():
    while True:
        print("Updating MongoDB")
        updateTrades()
        updateOrders()
        time.sleep(30)

if __name__ == "__main__":
    main()
