from schema import Trade, Order
import json
import time
from mongoengine import Document, StringField, IntField, FloatField, connect
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

def main():
    while True:
        updateTrades()
        time.sleep(60)

if __name__ == "__main__":
    main()
