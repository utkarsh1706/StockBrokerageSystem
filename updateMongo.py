from schema import Trade, Orders
import json
import time
from mongoengine import connect
import redis
from dotenv import load_dotenv
import os

load_dotenv()

mongoURI = os.getenv("mongoURI")

connect(db="StockBrokerSystem", host = mongoURI)

redisClient = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

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
            oid = orderData['oid']
            
            existingOrder = Orders.objects(oid=oid).first()
            
            if existingOrder:
                # Update existing order
                existingOrder.update(
                    price=float(orderData['price']),
                    quantity=float(orderData['quantity']),
                    filledQuantity=float(orderData['filledQuantity']),
                    averagePrice=float(orderData['averagePrice']),
                    lastUpdatesTimestamp=int(orderData['lastUpdatesTimestamp']),
                    status=orderData['status'],
                    side=orderData['side']
                )
            else:
                # Create a new order if it doesn't exist
                newOrder = Orders(
                    oid=oid,
                    price=float(orderData['price']),
                    quantity=float(orderData['quantity']),
                    filledQuantity=float(orderData['filledQuantity']),
                    averagePrice=float(orderData['averagePrice']),
                    placedTimestamp=int(orderData['placedTimestamp']),
                    lastUpdatesTimestamp=int(orderData['lastUpdatesTimestamp']),
                    status=orderData['status'],
                    side=orderData['side'],
                    clientOrderId=orderData['clientOrderId']
                )
                newOrder.save()
                print(f"Saved new order: {newOrder.oid}")

def main():
    while True:
        print("Updating MongoDB")
        updateTrades()
        updateOrders()
        time.sleep(60)

if __name__ == "__main__":
    main()
