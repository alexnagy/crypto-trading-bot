import logging, traceback
import time
from datetime import datetime
from engine.order import Order
from engine.exec_type import ExecType
from engine.basic_position_manager import BasicPositionManager
from engine.basic_order_manager import BasicOrderManager

class AbstractAlgo:

    TICK_RULE = "tickRule"
    LOT_SIZE = "lotSize"

    SATOSHI_RULE = 0.00000001

    def __init__(self, orderManager, mdataProvider):
        self.om = orderManager
        self.mdata = mdataProvider
        self.pm = BasicPositionManager()

        self.lastTrade = None
        self.pendingBuyRisk = 0
        self.currentBuyRisk = 0
        self.pendingSellRisk = 0
        self.currentSellRisk = 0
        self.currentPosition = 0
        self.avgTicketExecPrice = 0

        self.buyOrders = dict()
        self.sellOrders = dict()

        self.updatesCount = dict()

    def getName(self):
        return self.getClOrdIdPrefix()

    def getClOrdIdPrefix(self):
        return ""

    def initialize(self, config):
        self.tickRule = config.getParam(self.TICK_RULE, self.SATOSHI_RULE)
        self.lotSize = config.getParam(self.LOT_SIZE, self.SATOSHI_RULE)

    def onNewDay(self):
        logging.info(self.getName() + " READY TO TRADE")

    def onTrade(self, trade):
        code = trade.symbol.nativeCode
        self.lastTrade = trade

        count = self.updatesCount.get(code)
        if count is None:
            logging.info(self.getNow() + " Got marketdata for " + code)
            self.updatesCount[code] = 1
        else:
            count = count + 1
            self.updatesCount[code] = count
            if count % 10000 == 0:
                logging.info(self.getNow() + " Got " + str(count) + " marketdata updates for " + code + ", last price " + str(trade.price))
                if not self.isZeroQty(self.currentPosition):
                    self.logRisk()

        if self.lastTrade is not None and not self.isZeroPrice(self.lastTrade.price):
            self.pm.markPnl(self.lastTrade.price)


    def isZeroQty(self, v):
        return abs(v) < self.lotSize

    def isZeroPrice(self, v):
        return abs(v) < self.tickRule

    def logRisk(self):
        logging.info(self.getNow() + " Current buy risk: " + str(self.currentBuyRisk) +
                     ", currenty sell risk: " + str(self.currentSellRisk) +
                     ", current position: " + str(self.currentPosition))
        logging.info(self.getNow() + "  Total PnL: " + str(self.pm.getPnl()) +
                     ", realized PnL: " + str(self.pm.getRealizedPnl()) +
                     ", unrealized PnL: " + str(self.pm.getUnrealizedPnl()) +
                     ", traded notional: " + str(self.pm.getTradedNotional()))

    def getNow(self):
        timestamp = float(self.lastTrade.timestamp) / 1000 if self.lastTrade is not None else time.time()
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")


    def orderRemoved(self, orderId):
        if orderId is not None:
            self.buyOrders.pop(orderId, None)
            self.sellOrders.pop(orderId, None)

    def cancelAllOrders(self):
        self.cancelBuyOrders()
        self.cancelSellOrders()

    def cancelBuyOrders(self):
        for order in self.buyOrders.values():
            try:
                logging.info(self.getNow() + " Cancel buy order " + order.clientOrderId)
                self.cancelOrder(order)
            except:
                logging.error("Failed order cancel for " + order.clientOrderId)
                logging.error(traceback.format_exc())

    def cancelSellOrders(self):
        for order in self.sellOrders.values():
            try:
                logging.info(self.getNow() + " Cancel sell order " + order.clientOrderId)
                self.cancelOrder(order)
            except:
                logging.error("Failed order cancel for " + order.clientOrderId)
                logging.error(traceback.format_exc())


    def cancelOrder(self, order):
        if not order.pendingCancel:
            order.pendingCancel = True
            self.om.cancelOrder(order.exchange, order.symbol, order.orderId)

    def sendOrder(self, exchange, symbol, price, quantity, marginType, postOnly):
        if self.isZeroQty(quantity):
            return

        try:
            clOrdId = BasicOrderManager.getUniqueClOrdId(self.getClOrdIdPrefix())
            logging.info(self.getNow() + " Sending order " + clOrdId + " of " + str(quantity) + " at " + str(price))
            side = BasicOrderManager.BUY if quantity > 0 else BasicOrderManager.SELL
            quantity = abs(quantity)
            orderId = self.om.sendOrder(clOrdId, exchange, symbol, side, quantity, price, None, marginType, postOnly)

            if orderId is not None:
                if BasicOrderManager.isBuy(side):
                    self.pendingBuyRisk += quantity
                    self.buyOrders[orderId] = Order(orderId, clOrdId, exchange, symbol, side, quantity, price)
                else:
                    self.pendingSellRisk += quantity
                    self.sellOrders[orderId] = Order(orderId, clOrdId, exchange, symbol, side, quantity, price)
        except:
            logging.error("Failed sending order")
            logging.error(traceback.format_exc())

    def getOwnOrder(self, orderId):
        order = self.buyOrders.get(orderId)
        return order if order is not None else self.sellOrders.get(orderId)

    def onExecution(self, update):
        logging.info(self.getNow() + " Received execution of type " + str(update.execType) + " " + str(update))
        orderId = update.orderId

        if orderId is None:
            return

        logging.info(self.getNow() + " Execution orderId " + orderId)
        isAck = ExecType.NEW == update.execType
        isCancel = ExecType.CANCELED == update.execType or ExecType.EXPIRED == update.execType
        isFill = ExecType.FILL == update.execType or ExecType.PARTIAL_FILL == update.execType
        isReject = ExecType.REJECTED == update.execType

        clOrdId = update.clientOrderId
        if clOrdId is None:
            logging.info(self.getNow() + " Ignoring order with no client order id " + orderId)
            return

        order = self.getOwnOrder(orderId)
        if order is None:
            logging.info(self.getNow() + " Ignoring order not owned by current run, orderId = " + orderId)
            return

        isBuy = BasicOrderManager.isBuy(order.side)
        if isAck:
            logging.info(self.getNow() + " Received ack for " + orderId)
            quantity = abs(order.quantity)

            if isBuy:
                self.pendingBuyRisk -= quantity
                self.currentBuyRisk += quantity
            else:
                self.pendingSellRisk -= quantity
                self.currentSellRisk += quantity
        elif isReject:
            logging.info(self.getNow() + " Received reject for " + orderId)
            quantity = abs(order.remainingQuantity)
            self.orderRemoved(orderId)

            if isBuy:
                self.pendingBuyRisk -= quantity
            else:
                self.pendingSellRisk -= quantity
        elif isCancel:
            logging.info(self.getNow() + " Received cancel for " + orderId)
            quantity = abs(order.remainingQuantity)
            self.orderRemoved(orderId)

            if isBuy:
                self.currentBuyRisk -= quantity
            else:
                self.currentSellRisk -= quantity
        elif isFill:
            logging.info(self.getNow() + " Received fill for " + orderId + " " + str(update.quantity) + " at " + str(update.price))
            oldPosition = self.currentPosition
            remainingQty = max(abs(order.remainingQuantity - update.quantity), 0)
            order.remainingQuantity = remainingQty
            if self.isZeroQty(remainingQty):
                self.orderRemoved(orderId)

            fillPrice = update.price
            filledQty = update.quantity

            if isBuy:
                self.currentBuyRisk -= filledQty
                self.currentPosition += filledQty
            else:
                self.currentSellRisk -= abs(filledQty)
                self.currentPosition -= abs(filledQty)

            if self.isZeroQty(self.currentPosition):
                self.avgTicketExecPrice = 0
            else:
                self.avgTicketExecPrice = abs((oldPosition * self.avgTicketExecPrice + filledQty * fillPrice) / self.currentPosition)

            self.pm.onFill(fillPrice, filledQty)

            self.logRisk()
