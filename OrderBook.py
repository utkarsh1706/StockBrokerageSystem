import numpy as np
from LinkedList import DoublyLinkedList
from sortedcontainers import SortedDict
from threading import Lock
from Order import Order
from constants import *

class OrderBook:
    def __init__(self, bidlevels, asklevels, ws) -> None:
        self.doubleLLAsk = np.array([DoublyLinkedList() for _ in range(asklevels)], dtype=object)
        self.doubleLLBid = np.array([DoublyLinkedList() for _ in range(bidlevels)], dtype=object)
        self.orderMapBid = SortedDict(lambda x: -x)
        self.orderMapAsk = SortedDict()
        self.orderNode = {}
        self.orderInfo = {}
        self.ws = ws
    
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
            idx = (upperCircuit - price) * actualPricePrecision
            self._updateOrderMap(self.orderMapAsk, price, quantity)
            newNode = self.doubleLLAsk[idx].append(oid, quantity)
        else:
            idx = (price - lowerCircuit) * actualPricePrecision
            self._updateOrderMap(self.orderMapBid, price, quantity)
            newNode = self.doubleLLBid[idx].append(oid, quantity)
        
        self.orderNode[oid] = newNode
        return
    
    # def executeOrder(self):
    #     iteratorBid = iter(self.orderMapBid.items())
    #     iteratorAsk = iter(self.orderMapAsk.items())
    #     bestBidPrice, bestBidQuantity = next(iteratorBid)
    #     bestAskPrice, bestAskQuantity = next(iteratorAsk)
    #     while bestAskPrice and bestBidPrice and bestBidPrice >= bestAskPrice:
    #         bestBidNode = self.doubleLLBid[bestBidPrice]
    #         bestAskNode = self.doubleLLAsk[bestAskPrice]
    #         frontBid = bestBidNode.head
    #         frontAsk = bestAskNode.head
    #         if orderInfo[frontBid].lastUpdatesTimestamp > orderInfo[frontAsk].lastUpdatesTimestamp:
    #             #Ask price trade
    #             #quantity min of 2
    #             pass
            
    #         bestBidPrice, bestBidQuantity = next(iteratorBid)
    #         bestAskPrice, bestAskQuantity = next(iteratorAsk)

    def cancelOrder(self, price, unfilledQuantity, oid, side):
        nodePointer = self.orderNode[oid]
        del self.orderNode[oid]
        
        if side == "SELL":
            self.orderMapAsk[price] -= unfilledQuantity
            idx = (upperCircuit - price) * actualPricePrecision
            self.doubleLLAsk[idx].remove(nodePointer)
            self._removeOrderIfZero(self.orderMapAsk, price)
        else:
            self.orderMapBid[price] -= unfilledQuantity
            idx = (price - lowerCircuit) * actualPricePrecision
            self.doubleLLBid[idx].remove(nodePointer)
            self._removeOrderIfZero(self.orderMapBid, price)
        return

    def modifyOrder(self, initialPrice, updatePrice, unfilledQuantity, side, oid):
        nodePointer = self.orderNode[oid]
        
        if side == "SELL":
            self.orderMapAsk[initialPrice] -= unfilledQuantity
            self._updateOrderMap(self.orderMapAsk, updatePrice, unfilledQuantity)
            idx = (upperCircuit - initialPrice) * actualPricePrecision
            self.doubleLLAsk[idx].remove(nodePointer)
            idx = (upperCircuit - updatePrice) * actualPricePrecision
            newNode = self.doubleLLAsk[idx].append(oid, unfilledQuantity)
            self._removeOrderIfZero(self.orderMapAsk, initialPrice)
        else:
            self.orderMapBid[initialPrice] -= unfilledQuantity
            self._updateOrderMap(self.orderMapBid, updatePrice, unfilledQuantity)
            idx = (initialPrice - lowerCircuit) * actualPricePrecision
            self.doubleLLBid[idx].remove(nodePointer)
            idx = (updatePrice - lowerCircuit) * actualPricePrecision
            newNode = self.doubleLLBid[idx].append(oid, unfilledQuantity)
            self._removeOrderIfZero(self.orderMapBid, initialPrice)

        self.orderNode[oid] = newNode
        return
    
    def getOrderInfo(self, oid):
        order = self.orderInfo.get(oid)
        return order
    
    def addOrderInfo(self, oid, order:Order):
        self.orderInfo[oid] = order
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