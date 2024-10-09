from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from Order import Order
from OrderBook import OrderBook
import time
import threading
from redis import Redis
from constants import *
from helper import *

app = Flask(__name__)
socketio = SocketIO(app)

redis_client = Redis(host='localhost', port=6379)

# Initialize the Limiter with default rate limiting settings and redis as the storage backend
limiter = Limiter(get_remote_address, app=app, default_limits=["1000 per minute"], storage_uri="redis://localhost:6379")

orderBook = OrderBook(20)
orderDict = {}

@app.route('/api/place_order', methods=['POST'])
@limiter.limit("100 per minute")
def placeOrderAPI():
    print("Received request for placing an order")
    data = request.json
    print("Data received:", data)

    if not data or 'quantity' not in data or 'price' not in data or 'side' not in data:
        return jsonify({"error": "Invalid data"}), 400

    side = "SELL" if data['side'] == 1 else "BUY"
    
    data['price'] = round(data['price'], pricePrecision)

    isValid = checkValid(data['price'], data['quantity'], minOrderValue)

    if not isValid:
        return jsonify({"error": "Invalid Order"}), 400
    
    newOrder = Order(data['price'], data['quantity'], side)
    orderDict[newOrder.oid] = newOrder
    orderBook.placeOrder(data['price'], data['quantity'], newOrder.oid, side)
    
    return jsonify({"status": "success", "order_id": newOrder.oid}), 201

@app.route('/api/modify_order', methods=['PUT'])
@limiter.limit("100 per minute")
def modifyOrderAPI():
    
    print("Received request for modifying an order")
    data = request.json
    print("Data received:", data)

    if not data or 'order_id' not in data or 'price' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    order = orderDict.get(data['order_id'])
    if not order:
        return jsonify({"error": "Invalid Order_ID"}), 400
    
    isSucessful, initialPrice, quantity, side = order.modifyOrder(data['price'])
    
    if not isSucessful:
        return jsonify({"success": True, "message": "Order already Filled/Canceled"}), 200
    
    orderBook.modifyOrder(initialPrice, data['price'], quantity, side, order.oid)

    return jsonify({"success": True, "message": "Order modified successfully"}), 200

@app.route('/api/cancel_order', methods=['DELETE'])
@limiter.limit("100 per minute")
def cancelOrderAPI():
    
    print("Received request for canceling an order")
    data = request.json
    print("Data received:", data)

    if not data or 'order_id' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    order = orderDict.get(data['order_id'])
    if not order:
        return jsonify({"error": "Invalid Order_ID"}), 400
    
    isSuccessful, price, unFilledQuantity, side = order.cancelOrder()
    
    if not isSuccessful:
        return jsonify({"success": False, "message": "Order already Filled/Canceled"}), 200
    
    orderBook.cancelOrder(price, unFilledQuantity, data['order_id'], side)

    return jsonify({"success": True, "message": "Order canceled successfully"}), 200

@app.route('/api/fetch_order', methods=['GET'])
@limiter.limit("100 per minute")
def fetchOrderAPI():
    
    print("Received request for fetching an order")
    data = request.json
    print("Data received:", data)

    if not data or 'order_id' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    order = orderDict.get(data['order_id'])
    if not order:
        return jsonify({"error": "Invalid Order_ID"}), 400
    
    orderInfo = order.fetchOrder()

    return jsonify({"success": True, "data": orderInfo}), 200

def sendOrderBookUpdates():
    while True:
        time.sleep(1) 
        orderBookData = orderBook.getOrderBookData()
        socketio.emit('orderBook', {'data': orderBookData})
        print("Emitting OrderBook")

# Start the background thread when the Flask app starts
@app.before_request
def start_background_thread():
    if not hasattr(start_background_thread, "thread_started"):
        thread = threading.Thread(target=sendOrderBookUpdates)
        thread.daemon = True
        thread.start()
        start_background_thread.thread_started = True

@socketio.on('send_update') 
def handle_send_update(message):
    print('Received update:', message)
    socketio.emit('receive_update', {'data': 'Update received: ' + message['data']})

if __name__ == '__main__':
    socketio.run(app, debug=True)