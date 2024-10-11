from mongoengine import Document, StringField, IntField, FloatField, ListField, EnumField

# Define the Trade Document
class Trade(Document):
    unique_id = StringField(required=True, unique=True)
    execution_timestamp = IntField(required=True)
    price = FloatField(required=True)
    qty = FloatField(required=True)
    bid_order_id = StringField(required=True)
    ask_order_id = StringField(required=True)

# Define the Order Document
class Order(Document):
    oid = StringField(required=True, unique=True)
    price = FloatField(required=True)
    quantity = FloatField(required=True)
    filledQuantity = FloatField(default=0)
    averagePrice = FloatField(default=0)
    placedTimestamp = IntField(required=True)
    lastUpdatesTimestamp = IntField(required=True)
    side = EnumField(choices=['BUY', 'SELL'], required=True)
    status = EnumField(choices=['OPEN', 'CLOSED', 'CANCELLED', 'FILLED', 'PARTIALLY FILLED'], default='OPEN')
    clientOrderId = StringField()