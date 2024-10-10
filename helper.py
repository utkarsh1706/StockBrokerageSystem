from constants import *
import time
import uuid

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
