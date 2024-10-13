from schema import Orders
from Order import Order

def retrieveAndTraverseOrders(orderBook):
    print("Retreiving Data from MongoDB")
    orders = Orders.objects.order_by('placedTimestamp')  # Ascending order

    for order in orders:
        if order.status in ["CANCELED", "FILLED", "PARTIALLY CANCELED"]:
            continue
        newOrder = Order(price = order.price, quantity = order.quantity, side = order.side, clientOrderId = order.clientOrderId)
        newOrder.updateFromMongo(order.oid, order.filledQuantity, order.averagePrice, order.placedTimestamp, order.lastUpdatesTimestamp, order.status, order.clientOrderId)
        orderBook.addOrderInfo(newOrder.oid, newOrder)
        orderBook.placeOrder(order.price, order.quantity - order.filledQuantity, order.oid, order.side)
        orderBook.executeOrder()