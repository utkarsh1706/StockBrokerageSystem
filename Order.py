import time
import random
import string

class Order:
    def __init__(self, price, quantity, side, clientOrderId=None) -> None:
        self.price = price
        self.quantity = quantity
        self.filledQuantity = 0
        self.averagePrice = 0
        self.placedTimestamp = int(time.time())
        self.lastUpdatesTimestamp = self.placedTimestamp
        self.side = side
        self.status = "OPEN"
        self.clientOrderId = clientOrderId if clientOrderId is not None else self.generateClientID()

    def validation(self, price, quantity, minOrderValue, lowerCircuit, upperCircuit):
        if price < lowerCircuit:
            print("Lower Circuit")
            return False
        if price > upperCircuit:
            print("Upper Circuit")
            return False
        if price * quantity < minOrderValue:
            print("Minimum Order Value Condition not fulfilled!")
            return False
        
        return True
    
    def generateClientID(self):
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        random_letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
        return f"ORD-{timestamp}-{random_letters}-{random_suffix}"

    def cancelOrder(self):
        if self.status in ["CANCELED", "PARTIALLY CANCELED"]:
            print("Order already canceled!")
            return False, None, None, None
        
        if self.status == "FILLED":
            print("Order is already filled. Unable to cancel the Order")
            return False, None, None, None
        
        if self.filledQuantity > 0:
            self.status = "PARTIALLY CANCELED"
        else:
            self.status = "CANCELED"
        
        self.lastUpdatesTimestamp = int(time.time())

        return True, self.price, (self.quantity - self.filledQuantity), self.side
