import logging
from engine.order import Order
from engine.currency import Currency
from engine.execution import Execution
from engine.exec_type import ExecType
from engine.basic_order_manager import BasicOrderManager

class Simulator:
    def __init__(self, exchange):
        self.exchange = exchange
        self.listeners = []

        self.executionsToDispatch = []
        self.pendingOrders = dict()

        self.lastTrade = None

    def addListener(self, listener):
        self.listeners.append(listener)

    def start(self, apiKey, secret):
        pass

    def stop(self):
        pass

    def getNow(self):
        return self.lastTrade.timestamp

    def placeLimitOrder(self, clOrdId,  symbol, side,  quantity,  price, stopPrice, marginType, postOnly):
        orderId = BasicOrderManager.getUniqueClOrdId("O")
        self.pendingOrders[orderId] = Order(orderId, clOrdId, self.exchange, symbol, side, quantity, price)

        execution = Execution(BasicOrderManager.getUniqueClOrdId("E"),
                  orderId,
                  clOrdId,
                  ExecType.NEW,
                  Currency.fromNativeCode(self.exchange, symbol),
                  price,
                  quantity,
                  0,
                  self.getNow())

        self.queueExecution(execution)
        return orderId

    def cancelOrder(self, symbol, orderId):
        order = self.pendingOrders.pop(orderId, None)
        if order is not None:
            execution = Execution(BasicOrderManager.getUniqueClOrdId("E"),
                      orderId,
                      order.clientOrderId,
                      ExecType.CANCELED,
                      Currency.fromNativeCode(self.exchange, symbol),
                      order.price,
                      order.quantity,
                      0,
                      self.getNow())

            self.queueExecution(execution)
        else:
            logging.info("Order not existing or already canceled " + str(orderId))

    def queueExecution(self, e):
        self.executionsToDispatch.append(e)

    def dispatchExecutions(self):
        to_dispatch = self.executionsToDispatch.copy()
        self.executionsToDispatch = []

        for e in to_dispatch:
            self.dispatchExecution(e)

    def dispatchExecution(self, e):
        for listener in self.listeners:
            listener.onExecution(e)

    def onTrade(self, trade):
        self.lastTrade = trade
        self.dispatchExecutions()

        lastPrice = trade.price

        toRemove = []
        for order in self.pendingOrders.values():
            filled = False
            if BasicOrderManager.isBuy(order.side) and order.price > lastPrice:
                filled = True
            elif not BasicOrderManager.isBuy(order.side) and order.price < lastPrice:
                filled = True

            if filled:
                toRemove.append(order.orderId)

                execution = Execution(BasicOrderManager.getUniqueClOrdId("E"),
                        order.orderId,
                        order.clientOrderId,
                        ExecType.FILL,
                        Currency.fromNativeCode(self.exchange, order.symbol),
                        trade.price,
                        order.quantity if BasicOrderManager.isBuy(order.side) else -order.quantity,
                        0,
                        self.getNow())
                self.queueExecution(execution)


        for orderId in toRemove:
            self.pendingOrders.pop(orderId, None)
