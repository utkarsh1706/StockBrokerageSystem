from constants import *
import time
import uuid
import json

def checkValid(price, quantity, minOrderValue, side):
    if quantity <=0:
        return False, "Invalid Quantity"
    if (price >= upperCircuit or price <= lowerCircuit):
        return False, "Kindly place order within the circuit range!"
    if price*quantity < minOrderValue:
        return False, "MinOrderValue not satisfied"
    return True, "Order Valid!"

def generateTradeID():
    timestamp = int(time.time() * 1000)
    random_part = str(uuid.uuid4()).split('-')[0]
    trade_id = f"{timestamp}-{random_part}"
    return trade_id

def addTradeRedis(redisClient, data):
    try:
        jsonData = json.dumps(data)    
        redisClient.rpush("tradeData", jsonData)
    except json.JSONDecodeError as e:
        print(f"Error encoding data to JSON: {e}")
    except Exception as e:
        print(f"Error adding trade data to Redis: {e}")