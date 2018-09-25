import time
import logging
from engine.algo_config import AlgoConfig

id_counter = 0

class BasicOrderManager:

    BUY = "1"
    SELL = "2"

    CASH = "1"
    MARGIN_OPEN = "2"
    MARGIN_CLOSE = "3"

    def __init__(self, factory):
        self.factory = factory
        self.handlers = dict()
        self.listeners = []

    def addListener(self, listener):
        self.listeners.append(listener)

    def initialize(self, config):
        exchange = config.getParam(AlgoConfig.EXCHANGE)
        apiKey = config.getParam(AlgoConfig.API_KEY)
        secret = config.getParam(AlgoConfig.API_SECRET)

        ordersHandler = self.factory.get(exchange)
        ordersHandler.start(apiKey, secret)

        self.handlers[exchange] = ordersHandler
        ordersHandler.addListener(self)

    def sendOrder(self, clOrdId,
					 exchange,
					 symbol, side, quantity, price, stopPrice,
					 marginType, postOnly):
        handler = self.handlers[exchange]
        if handler is not None:
            return handler.placeLimitOrder(clOrdId, symbol, side, quantity, price, stopPrice, marginType, postOnly)
        else:
            logging.error("No handler registered for exchange " + exchange)
            return None

    def cancelOrder(self, exchange, symbol, orderId):
        handler = self.handlers[exchange]
        if handler is not None:
            handler.cancelOrder(symbol, orderId)
        else:
            logging.error("No handler registered for exchange " + exchange)

    def onExecution(self, e):
        for listener in self.listeners:
            listener.onExecution(e)

    @staticmethod
    def getUniqueClOrdId(prefix):
        global id_counter
        id_counter = id_counter + 1
        return prefix + "-" + str(int(time.time()))+ "-" + str(id_counter)

    @staticmethod
    def isBuy(side):
        return BasicOrderManager.BUY == side
