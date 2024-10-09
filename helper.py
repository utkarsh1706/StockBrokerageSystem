from constants import *

def checkValid(price, quantity, minOrderValue, side):
    if quantity <=0:
        return False, "Invalid Quantity"
    if side=="BUY" and price >= upperCircuit and upperCircuitValid:
        return False, "Upper Circuit!"
    if side=="SELL" and price <= lowerCircuit and lowerCircuitValid:
        return False, "Lower Circuit!"
    if price*quantity < minOrderValue:
        return False, "MinOrderValue not satisfied"
    return True, "Order Valid!"