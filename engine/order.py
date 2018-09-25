class Order:
    def __init__(self, orderId, clientOrderId, exchange, symbol, side, quantity, price):
        self.orderId = orderId
        self.clientOrderId = clientOrderId
        self.exchange = exchange
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.remainingQuantity = quantity
        self.pendingCancel = False