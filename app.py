from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from Order import Order
from OrderBook import OrderBook
import time
import threading
import redis
from constants import *
from helper import *
from retrieveMongo import *
from mongoengine import connect
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

mongoURI = os.getenv("mongoURI")
redisPassword = os.getenv("redisPassword")
redisHost = os.getenv("redisHost")
redisPort = os.getenv("redisPort")
storageRateLimit = os.getenv("storageRateLimit")

connect(db="StockBrokerSystem", host=mongoURI)

app = Flask(__name__)
socketio = SocketIO(app)

try:
    redisClient = redis.Redis(host=redisHost, port=redisPort, password=redisPassword)
    redisClient.ping()
    print("Connected to Redis")
except redis.ConnectionError as e:
    print("Redis not connected due to ", e)

# Initialize the Limiter with default rate limiting settings and redis as the storage backend
limiter = Limiter(get_remote_address, app=app, default_limits=["1000 per minute"], storage_uri=storageRateLimit)

orderBook = None
initialization_lock = threading.Lock()

@app.route('/api/place_order', methods=['POST'])
@limiter.limit("100 per minute")
def placeOrderAPI():
    try:
        print("Received request for placing an order")
        data = request.json
        print("Data received:", data)

        if not data or 'quantity' not in data or 'price' not in data or 'side' not in data:
            return jsonify({"error": "Invalid data"}), 400

        if data['side'] == 1:
            side = "SELL"
        elif data['side'] == -1:
            side = "BUY"
        else:
            return jsonify({"error": "Invalid Side"}), 400

        data['price'] = round(data['price'], pricePrecision)

        isValid, message = checkValid(data['price'], data['quantity'], minOrderValue, side)

        if not isValid:
            return jsonify({"error": message}), 400

        newOrder = Order(price=data['price'], quantity=data['quantity'], side=side)
        orderBook.addOrderInfo(newOrder.oid, newOrder)
        orderBook.placeOrder(data['price'], data['quantity'], newOrder.oid, side)
        orderBook.executeOrder()

        return jsonify({"status": "success", "order_id": newOrder.oid}), 201

    except KeyError as e:
        return jsonify({"error": f"Missing key in request data: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid value provided: {e}"}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/api/modify_order', methods=['PUT'])
@limiter.limit("100 per minute")
def modifyOrderAPI():
    try:
        print("Received request for modifying an order")
        data = request.json
        print("Data received:", data)

        if not data or 'order_id' not in data or 'price' not in data:
            return jsonify({"error": "Invalid data"}), 400

        order = orderBook.getOrderInfo(data['order_id'])
        if not order:
            return jsonify({"error": "Invalid Order_ID"}), 400

        isSucessful, initialPrice, quantity, side = order.modifyOrder(data['price'])

        if not isSucessful:
            return jsonify({"success": True, "message": "Order already Filled/Canceled"}), 200

        orderBook.addOrderRedis(order.oid, order)
        orderBook.modifyOrder(initialPrice, data['price'], quantity, side, order.oid)
        orderBook.executeOrder()

        return jsonify({"success": True, "message": "Order modified successfully"}), 200

    except KeyError as e:
        return jsonify({"error": f"Missing key in request data: {e}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid value provided: {e}"}), 400
    except AttributeError as e:
        return jsonify({"error": f"Attribute error: {e}"}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/api/cancel_order', methods=['DELETE'])
@limiter.limit("100 per minute")
def cancelOrderAPI():
    try:
        print("Received request for canceling an order")
        data = request.json
        print("Data received:", data)

        if not data or 'order_id' not in data:
            return jsonify({"error": "Invalid data"}), 400

        order = orderBook.getOrderInfo(data['order_id'])
        if not order:
            return jsonify({"error": "Invalid Order_ID"}), 400

        isSuccessful, price, unFilledQuantity, side = order.cancelOrder()

        if not isSuccessful:
            return jsonify({"success": False, "message": "Order already Filled/Canceled"}), 200

        orderBook.addOrderRedis(order.oid, order)
        orderBook.cancelOrder(price, unFilledQuantity, data['order_id'], side)

        return jsonify({"success": True, "message": "Order canceled successfully"}), 200

    except KeyError as e:
        return jsonify({"error": f"Missing key in request data: {e}"}), 400
    except AttributeError as e:
        return jsonify({"error": f"Attribute error: {e}"}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

def sendOrderBookUpdates():
    while True:
        time.sleep(1) 
        orderBookData = orderBook.getOrderBookData()
        print(orderBookData)
        socketio.emit('orderBook', {'data': orderBookData})
        # print("Emitting OrderBook")

# Start the background thread when the Flask app starts
@app.before_request
def initializeStart():
    global orderBook

    with initialization_lock:
        if not hasattr(initializeStart, "initialized"):
            try:
                lowerCircuitPrice = lastTradedPrice * (1 - lowerCircuitPercent)
                upperCircuitPrice = lastTradedPrice * (1 + upperCircuitPercent)

                levels = int((upperCircuitPrice - lowerCircuitPrice) * actualPricePrecision) + 1
                orderBook = OrderBook(levels, socketio, redisClient)
                retrieveAndTraverseOrders(orderBook)

                if not hasattr(initializeStart, "threadStarted"):
                    thread = threading.Thread(target=sendOrderBookUpdates)
                    thread.daemon = True
                    thread.start()
                    initializeStart.threadStarted = True
                
                updateMongoFile = os.path.join(os.path.dirname(__file__), 'updateMongo.py')
                # subprocess.Popen(['python', updateMongoFile])

                initializeStart.initialized = True

            except Exception as e:
                print(f"An error occurred during initialization: {e}")

if __name__ == '__main__':
    socketio.run(app, debug=True)