class Execution:
    def __init__(self, id, orderId, clientOrderId, execType, symbol, price, quantity, fees, timestamp):
        self.id = id
        self.orderId = orderId
        self.clientOrderId = clientOrderId
        self.execType = execType
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.fees = fees
        self.timestamp = timestamp

    def __str__(self):
        return "%s / %s %s / %d %s @ %f qty %f / %f / %d" % (self.id, self.orderId, self.clientOrderId, self.execType, self.symbol, self.price, self.quantity, self.fees, self.timestamp)
