from schema import *
from Order import Order

def retrieveAndTraverseOrders(orderBook):
    try:
        print("Retrieving Data from MongoDB")
        orders = Orders.objects.order_by('placedTimestamp')
        print(orders)
        
        for order in orders:
            try:
                if order.status in [OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.PARTIALLY_CANCELED]:
                    continue
                newOrder = Order(price=order.price, quantity=order.quantity, side=order.side.name, clientOrderId=order.clientOrderId)
                newOrder.updateFromMongo(order.oid, order.filledQuantity, order.averagePrice, order.placedTimestamp, order.lastUpdatesTimestamp, order.status.name, order.clientOrderId)
                orderBook.addOrderInfo(newOrder.oid, newOrder)
                orderBook.placeOrder(order.price, order.quantity - order.filledQuantity, order.oid, order.side.name)
                orderBook.executeOrder()
                
            except AttributeError as e:
                print(f"Attribute error while processing order {order.oid}: {e}")
            except ValueError as e:
                print(f"Value error while processing order {order.oid}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing order {order.oid}: {e}")

    except Exception as e:
        print(f"Error retrieving orders from MongoDB: {e}")