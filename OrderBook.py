import numpy as np
from LinkedList import DoublyLinkedList

class OrderBook:
    def __init__(self, levels) -> None:
        self.levels = levels
        self.doubleLLAsk = np.array([DoublyLinkedList() for _ in range(levels)], dtype=object)
        self.doubleLLBid = np.array([DoublyLinkedList() for _ in range(levels)], dtype=object)
        self.orderMapBid = {}
        self.orderMapAsk = {}
        self.orderNode = {}
    
    def generateOrderID(self):
        pass

    def cancelOrder(self, price, unfilledQuantity, oid, side):
        nodePointer = self.orderNode[oid]
        del self.orderNode[oid]
        if side == "SELL":
            self.orderMapAsk[price] -= unfilledQuantity
            self.doubleLLAsk[price].remove(nodePointer)
            if self.orderMapAsk[price] == 0:
                del self.orderMapAsk[price]
        else:
            self.orderMapBid[price] -= unfilledQuantity
            self.doubleLLBid[price].remove(nodePointer)
            if self.orderMapBid[price] == 0:
                del self.orderMapBid[price]
        return
    
    def modifyOrder(self, initialPrice, updatePrice, unfilledQuantity, side, oid):
        
        nodePointer = self.orderNode[oid]

        if side == "SELL":
            self.orderMapAsk[initialPrice] -= unfilledQuantity
            self.orderMapAsk[updatePrice] += unfilledQuantity
            self.doubleLLAsk[initialPrice].remove(nodePointer)
            newNode = self.doubleLLAsk[updatePrice].append(oid, unfilledQuantity)
            if self.orderMapAsk[initialPrice] == 0:
                del self.orderMapAsk[initialPrice]
        else:
            self.orderMapBid[initialPrice] -= unfilledQuantity
            self.orderMapBid[updatePrice] -= unfilledQuantity
            self.doubleLLBid[initialPrice].remove(nodePointer)
            newNode = self.doubleLLBid[updatePrice].append(oid, unfilledQuantity)
            if self.orderMapBid[initialPrice] == 0:
                del self.orderMapBid[initialPrice]
        
        self.orderNode[oid] = newNode
        
        return
