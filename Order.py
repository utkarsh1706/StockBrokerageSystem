import time
import random
import string

class Order:
    def __init__(self, price, quantity, side, clientOrderId=None) -> None:
        self.oid = self.generateOrderId()
        self.price = price
        self.quantity = quantity
        self.filledQuantity = 0
        self.averagePrice = 0
        self.placedTimestamp = int(time.time())
        self.lastUpdatesTimestamp = self.placedTimestamp
        self.side = side
        self.status = "OPEN"
        self.clientOrderId = clientOrderId if clientOrderId is not None else self.generateClientID()

    def generateClientID(self):
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        random_letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(2))
        return f"CLIENTORD-{timestamp}-{random_letters}-{random_suffix}"
    
    def generateOrderId(self):
        timestamp = int(time.time())
        random_suffix = random.randint(100, 999)
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
    
    def modifyOrder(self, updatePrice):
        if self.status in ["CANCELED", "PARTIALLY CANCELED"]:
            print("Order already canceled!")
            return False, None, None, None
        
        if self.status == "FILLED":
            print("Order is already filled. Unable to modify the Order")
            return False, None, None, None
        
        initialPrice = self.price
        self.price = updatePrice

        self.lastUpdatesTimestamp = int(time.time())

        return True, initialPrice, (self.quantity - self.filledQuantity), self.side
    
    def fetchOrder(self):
        orderInfo = {
            "order_price" : self.price,
            "order_quantity" : self.quantity,
            "average_traded_price" : self.averagePrice,
            "traded_quantity" : self.filledQuantity,
            "order_alive" : 1 if self.status in ["OPEN", "PARTIALLY FILLED"] else 0
        }
        return orderInfo