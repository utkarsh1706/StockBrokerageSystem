import numpy as np
from LinkedList import DoublyLinkedList
from sortedcontainers import SortedDict
from threading import Lock
from Order import Order
import time
from constants import *
from helper import *
import threading

class OrderBook:
    def __init__(self, levels, ws, redisClient) -> None:
        self.doubleLLAsk = np.array([DoublyLinkedList() for _ in range(levels)], dtype=object)
        self.doubleLLBid = np.array([DoublyLinkedList() for _ in range(levels)], dtype=object)
        self.orderMapBid = SortedDict(lambda x: -x)
        self.orderMapAsk = SortedDict()
        self.orderNode = {}
        self.orderInfo = {}
        self.ws = ws
        self.redisClient = redisClient
        self.lock = threading.Lock()
    
    def _updateOrderMap(self, priceMap, price, quantity):
        if price in priceMap:
            priceMap[price] += quantity
        else:
            priceMap[price] = quantity
        return
    
    def _removeOrderIfZero(self, priceMap, price):
        if price in priceMap and priceMap[price] == 0:
            del priceMap[price]
        return
    
    def placeOrder(self, price, quantity, oid, side):
        with self.lock:
            try:
                if side == "SELL":
                    idx = int((upperCircuit - price) * actualPricePrecision)
                    self._updateOrderMap(self.orderMapAsk, price, quantity)
                    newNode = self.doubleLLAsk[idx].append(oid, quantity)
                else:
                    idx = int((price - lowerCircuit) * actualPricePrecision)
                    self._updateOrderMap(self.orderMapBid, price, quantity)
                    newNode = self.doubleLLBid[idx].append(oid, quantity)

                self.orderNode[oid] = newNode
                
            except KeyError as e:
                print(f"Key error: {e}. Order ID {oid} might not exist.")
            except ValueError as e:
                print(f"Value error: {e}. Invalid price or quantity.")
            except Exception as e:
                print(f"An unexpected error occurred while placing order {oid}: {e}")

    def emitTrade(self, price, fillQuantity, bidID, askID):
        
        tradeData = {
            "unique_id": generateTradeID(),
            "execution_timestamp": int(time.time()),
            "price": price,
            "qty": fillQuantity,
            "bid_order_id": bidID,
            "ask_order_id": askID
        }

        addTradeRedis(self.redisClient, tradeData)

        self.ws.emit("tradeUpdates", tradeData)
        print("Emitted Trade Data:", tradeData)
        return
    
    def getAllTrades(self):
        with self.lock:
            try:
                data = [json.loads(item) for item in self.redisClient.lrange('tradeData', 0, -1)]
                return data
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}. Failed to decode trade data.")
                return []
            except Exception as e:
                print(f"An unexpected error occurred while retrieving trades: {e}")
                return []
    
    def processOrder(self, askOrder, bidOrder, fillQuantity):
        try:
            price = bidOrder.price if askOrder.lastUpdatesTimestamp > bidOrder.lastUpdatesTimestamp else bidOrder.price
            
            askOrder.filledQuantity += fillQuantity
            bidOrder.filledQuantity += fillQuantity
            
            askOrder.averagePrice = round(((askOrder.averagePrice * (askOrder.filledQuantity - fillQuantity)) + (price * fillQuantity)) / askOrder.filledQuantity, 2)
            bidOrder.averagePrice = round(((bidOrder.averagePrice * (bidOrder.filledQuantity - fillQuantity)) + (price * fillQuantity)) / bidOrder.filledQuantity, 2)
            
            if askOrder.filledQuantity == askOrder.quantity:
                askOrder.status = "FILLED"
                askOrder.lastUpdatesTimestamp = int(time.time())
            else:
                askOrder.status = "PARTIALLY FILLED"

            if bidOrder.filledQuantity == bidOrder.quantity:
                bidOrder.status = "FILLED"
                bidOrder.lastUpdatesTimestamp = int(time.time())
            else:
                bidOrder.status = "PARTIALLY FILLED"

            self.emitTrade(price, fillQuantity, bidOrder.oid, askOrder.oid)
            self.addOrderRedis(askOrder.oid, askOrder)
            self.addOrderRedis(bidOrder.oid, bidOrder)
            
        except ZeroDivisionError as e:
            print(f"Zero division error: {e}. Check the filled quantities.")
        except Exception as e:
            print(f"An unexpected error occurred while processing order: {e}")

        return

    def executeOrder(self):
        with self.lock:
            try:
                iteratorBid = iter(self.orderMapBid.items())
                iteratorAsk = iter(self.orderMapAsk.items())
                bestBidPrice, bestBidQuantity = next(iteratorBid)
                bestAskPrice, bestAskQuantity = next(iteratorAsk)
            except StopIteration:
                return
            except Exception as e:
                print(f"An error occurred while initializing iterators: {e}")
                return

            while bestBidPrice is not None and bestAskPrice is not None and bestBidPrice >= bestAskPrice:
                bestBidNode = self.doubleLLBid[int((bestBidPrice - lowerCircuit) * actualPricePrecision)].head
                bestAskNode = self.doubleLLAsk[int((upperCircuit - bestAskPrice) * actualPricePrecision)].head

                while bestBidNode and bestAskNode and bestBidQuantity > 0 and bestAskQuantity > 0:
                    bidOrder = self.orderInfo[bestBidNode.order_id]
                    askOrder = self.orderInfo[bestAskNode.order_id]

                    fillQuantity = min(bidOrder.quantity - bidOrder.filledQuantity, askOrder.quantity - askOrder.filledQuantity)

                    # Process the order and update the quantities
                    try:
                        self.processOrder(askOrder, bidOrder, fillQuantity)
                    except Exception as e:
                        print(f"Error processing order: {e}")
                    bestAskQuantity -= fillQuantity
                    bestBidQuantity -= fillQuantity

                    # Move to the next nodes in the doubly linked lists if orders are filled
                    if askOrder.status == "FILLED":
                        tempNode = bestAskNode
                        del self.orderNode[tempNode.order_id]
                        bestAskNode = bestAskNode.next
                        self.doubleLLAsk[int((upperCircuit - bestAskPrice) * actualPricePrecision)].remove(tempNode)
                    if bidOrder.status == "FILLED":
                        tempNode = bestBidNode
                        del self.orderNode[tempNode.order_id]
                        bestBidNode = bestBidNode.next
                        self.doubleLLBid[int((bestBidPrice - lowerCircuit) * actualPricePrecision)].remove(tempNode)

                # Update order maps if any order is partially filled
                if bestAskQuantity <= 0:
                    self.orderMapBid[bestBidPrice] = bestBidQuantity
                if bestBidQuantity <= 0:
                    self.orderMapAsk[bestAskPrice] = bestAskQuantity

                # Move iteratorBid to the next price level only if bestBidNode is None
                if bestBidNode is None:
                    initPrice = bestBidPrice
                    bestBidPrice, bestBidQuantity = next(iteratorBid, (None, None))
                    del self.orderMapBid[initPrice]
                        
                # Move iteratorAsk to the next price level only if bestAskNode is None
                if bestAskNode is None:
                    initPrice = bestAskPrice
                    bestAskPrice, bestAskQuantity = next(iteratorAsk, (None, None))
                    del self.orderMapAsk[initPrice]

        return

    def cancelOrder(self, price, unfilledQuantity, oid, side):
        with self.lock:
            try:
                nodePointer = self.orderNode[oid]
                del self.orderNode[oid]
                
                if side == "SELL":
                    self.orderMapAsk[price] -= unfilledQuantity
                    idx = int((upperCircuit - price) * actualPricePrecision)
                    self.doubleLLAsk[idx].remove(nodePointer)
                    self._removeOrderIfZero(self.orderMapAsk, price)
                else:
                    self.orderMapBid[price] -= unfilledQuantity
                    idx = int((price - lowerCircuit) * actualPricePrecision)
                    self.doubleLLBid[idx].remove(nodePointer)
                    self._removeOrderIfZero(self.orderMapBid, price)
                    
            except KeyError as e:
                print(f"Key error: {e}. Order ID {oid} might not exist.")
            except ValueError as e:
                print(f"Value error: {e}. Invalid price or quantity.")
            except Exception as e:
                print(f"An unexpected error occurred while canceling order {oid}: {e}")

    def modifyOrder(self, initialPrice, updatePrice, unfilledQuantity, side, oid):
        with self.lock:
            try:
                nodePointer = self.orderNode[oid]
                
                if side == "SELL":
                    self.orderMapAsk[initialPrice] -= unfilledQuantity
                    self._updateOrderMap(self.orderMapAsk, updatePrice, unfilledQuantity)
                    idx = int((upperCircuit - initialPrice) * actualPricePrecision)
                    self.doubleLLAsk[idx].remove(nodePointer)
                    idx = int((upperCircuit - updatePrice) * actualPricePrecision)
                    newNode = self.doubleLLAsk[idx].append(oid, unfilledQuantity)
                    self._removeOrderIfZero(self.orderMapAsk, initialPrice)
                else:
                    self.orderMapBid[initialPrice] -= unfilledQuantity
                    self._updateOrderMap(self.orderMapBid, updatePrice, unfilledQuantity)
                    idx = int((initialPrice - lowerCircuit) * actualPricePrecision)
                    self.doubleLLBid[idx].remove(nodePointer)
                    idx = int((updatePrice - lowerCircuit) * actualPricePrecision)
                    newNode = self.doubleLLBid[idx].append(oid, unfilledQuantity)
                    self._removeOrderIfZero(self.orderMapBid, initialPrice)

                self.orderNode[oid] = newNode
                
            except KeyError as e:
                print(f"Key error: {e}. Order ID {oid} might not exist.")
            except ValueError as e:
                print(f"Value error: {e}. Invalid price or quantity.")
            except Exception as e:
                print(f"An unexpected error occurred while modifying order {oid}: {e}")

    def getOrderInfo(self, oid):
        order = self.orderInfo.get(oid)
        return order
    
    def addOrderInfo(self, oid, order:Order):
        with self.lock:
            self.orderInfo[oid] = order
            self.addOrderRedis(oid, order)
        return
    
    def addOrderRedis(self, oid, order: Order):
        orderKey = f"order:{oid}"
        orderData = order.to_dict()
        orderData['side'] = str(order.side)
        orderData['status'] = str(order.status)
        self.redisClient.hset(orderKey, mapping=orderData)
        # print(f"Order {order.oid} stored in Redis with key: {orderKey}")
        return
    
    def getOrderBookData(self):

        with self.lock:
            bestBids = list(self.orderMapBid.items())[:5]
            bestAsks = list(self.orderMapAsk.items())[:5]

            bids = [[price, quantity] for price, quantity in bestBids]  # Highest bids first

            asks = [[price, quantity] for price, quantity in bestAsks]  # Lowest asks first

            # Return as a dictionary
            return {
                "asks": asks,
                "bids": bids
            }