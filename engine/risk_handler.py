class RiskHandler:
    def __init__(self, orderManager):
        self.orderManager = orderManager
        self.orderManager.addListener(self)

        self.listeners = []

    def addListener(self, listener):
        self.listeners.append(listener)

    def initialize(self, config):
        self.orderManager.initialize(config)

    def sendOrder(self, clOrdId,
					 exchange,
					 symbol, side, quantity, price, stopPrice,
					 marginType, postOnly):
        return self.orderManager.sendOrder(clOrdId, exchange, symbol, side, quantity, price, stopPrice, marginType, postOnly)

    def cancelOrder(self, exchange, symbol, orderId):
        self.orderManager.cancelOrder(exchange, symbol, orderId)

    def onExecution(self, e):
        for listener in self.listeners:
            listener.onExecution(e)

    def onTrade(self, trade):
        # mark to market and handle overall risk
        pass