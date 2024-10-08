from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from Order import Order
from OrderBook import OrderBook
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app)

orderBook = OrderBook(20)
orderDict = {}

@app.route('/api/place_order', methods=['POST'])
def placeOrderAPI():
    print("Received request for placing an order")
    data = request.json
    print("Data received:", data)

    if not data or 'quantity' not in data or 'price' not in data or 'side' not in data:
        return jsonify({"error": "Invalid data"}), 400

    side = "SELL" if data['side'] == 1 else "BUY"
    newOrder = Order(data['price'], data['quantity'], side)
    orderDict[newOrder.oid] = newOrder
    orderBook.placeOrder(data['price'], data['quantity'], newOrder.oid, side)
    
    return jsonify({"status": "success", "order_id": newOrder.oid}), 201

@app.route('/api/modify_order', methods=['PUT'])
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

def sendOrderBookUpdates():
    while True:
        time.sleep(1) 
        orderBookData = orderBook.getOrderBookData()
        socketio.emit('orderBook', {'data': orderBookData})

# Start the background thread when the Flask app starts
@app.before_first_request
def start_background_thread():
    thread = threading.Thread(target=sendOrderBookUpdates)
    thread.daemon = True
    thread.start()

@socketio.on('send_update') 
def handle_send_update(message):
    print('Received update:', message)
    socketio.emit('receive_update', {'data': 'Update received: ' + message['data']})

if __name__ == '__main__':
    socketio.run(app, debug=True)