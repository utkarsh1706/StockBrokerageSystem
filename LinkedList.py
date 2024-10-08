class Node:
    def __init__(self, order_id, quantity):
        self.order_id = order_id
        self.quantity = quantity
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, order_id, quantity):
        new_node = Node(order_id, quantity)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        return new_node

    def remove(self, node):
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        if node == self.head:
            self.head = node.next
        if node == self.tail:
            self.tail = node.prev

    def display(self):
        current = self.head
        while current:
            print(f"OrderID: {current.order_id}, Quantity: {current.quantity}")
            current = current.next
