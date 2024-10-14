from schema import *
from Order import Order

def retrieveAndTraverseOrders(orderBook):
    print("Retreiving Data from MongoDB")
    orders = Orders.objects.order_by('placedTimestamp')

    for order in orders:
        if order.status in [OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.PARTIALLY_CANCELED]:
            continue
        newOrder = Order(price = order.price, quantity = order.quantity, side = order.side.name, clientOrderId = order.clientOrderId)
        newOrder.updateFromMongo(order.oid, order.filledQuantity, order.averagePrice, order.placedTimestamp, order.lastUpdatesTimestamp, order.status.name, order.clientOrderId)
        orderBook.addOrderInfo(newOrder.oid, newOrder)
        orderBook.placeOrder(order.price, order.quantity - order.filledQuantity, order.oid, order.side.name)
        orderBook.executeOrder()