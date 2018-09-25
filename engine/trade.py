class Trade:
    def __init__(self, id, symbol, price, quantity, timestamp):
        self.id = id
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp

    def __str__(self):
        return "%s %s @ %f qty %f / %d" % (self.id, self.symbol, self.price, self.quantity, self.timestamp)
