import numpy as np
from LinkedList import DoublyLinkedList
from sortedcontainers import SortedDict

class OrderBook:
    def __init__(self, levels) -> None:
        self.levels = levels
        self.doubleLLAsk = np.array([DoublyLinkedList() for _ in range(levels)], dtype=object)
        self.doubleLLBid = np.array([DoublyLinkedList() for _ in range(levels)], dtype=object)
        self.orderMapBid = SortedDict()
        self.orderMapAsk = SortedDict()
        self.orderNode = {}
    
    def _updateOrderMap(self, price_map, price, quantity):
        if price in price_map:
            price_map[price] += quantity
        else:
            price_map[price] = quantity
        return
    
    def _removeOrderIfZero(self, price_map, price):
        if price in price_map and price_map[price] == 0:
            del price_map[price]
        return
    
    def placeOrder(self, price, quantity, oid, side):
        if side == "SELL":
            self._updateOrderMap(self.orderMapAsk, price, quantity)
            newNode = self.doubleLLAsk[price].append(oid, quantity)
        else:
            self._updateOrderMap(self.orderMapBid, price, quantity)
            newNode = self.doubleLLBid[price].append(oid, quantity)
        
        self.orderNode[oid] = newNode
        return

    def cancelOrder(self, price, unfilledQuantity, oid, side):
        nodePointer = self.orderNode[oid]
        del self.orderNode[oid]
        
        if side == "SELL":
            self.orderMapAsk[price] -= unfilledQuantity
            self.doubleLLAsk[price].remove(nodePointer)
            self._removeOrderIfZero(self.orderMapAsk, price)
        else:
            self.orderMapBid[price] -= unfilledQuantity
            self.doubleLLBid[price].remove(nodePointer)
            self._removeOrderIfZero(self.orderMapBid, price)
        return

    def modifyOrder(self, initialPrice, updatePrice, unfilledQuantity, side, oid):
        nodePointer = self.orderNode[oid]
        
        if side == "SELL":
            self.orderMapAsk[initialPrice] -= unfilledQuantity
            self._updateOrderMap(self.orderMapAsk, updatePrice, unfilledQuantity)
            self.doubleLLAsk[initialPrice].remove(nodePointer)
            newNode = self.doubleLLAsk[updatePrice].append(oid, unfilledQuantity)
            self._removeOrderIfZero(self.orderMapAsk, initialPrice)
        else:
            self.orderMapBid[initialPrice] -= unfilledQuantity
            self._updateOrderMap(self.orderMapBid, updatePrice, unfilledQuantity)
            self.doubleLLBid[initialPrice].remove(nodePointer)
            newNode = self.doubleLLBid[updatePrice].append(oid, unfilledQuantity)
            self._removeOrderIfZero(self.orderMapBid, initialPrice)

        self.orderNode[oid] = newNode
        return
    
    def getOrderBookData(self):
        
        bestBids = list(self.orderMapBid.items())[-5:]
        bestAsks = list(self.orderMapAsk.items())[:5]

        bids = [[price, quantity] for price, quantity in reversed(bestBids)]  # Highest bids first

        asks = [[price, quantity] for price, quantity in bestAsks]  # Lowest asks first

        # Return as a dictionary
        return {
            "bids": bids,
            "asks": asks
        }