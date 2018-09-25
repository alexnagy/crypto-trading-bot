import time
import math
import logging
from engine.abstract_algo import AbstractAlgo
from engine.basic_order_manager import BasicOrderManager

class BasicTradingAlgo(AbstractAlgo):
    SUBMIT_DISTANCE_CFG = "submitDistanceBps"
    STOP_PROFIT_CFG = "stopProfitBps"
    STOP_LOSS_CFG = "stopLossBps"
    ORDER_QUANTITY_CFG = "orderQuantity"
    ORDERS_COUNT_CFG = "ordersCount"
    ALLOW_SHORT_CFG = "allowShort"
    ALLOW_LONG_CFG = "allowLong"
    MARGIN_CFG = "margin"
    POST_ONLY_CFG = "postOnly"

    def __init__(self, orderManager, mdataProvider):
        AbstractAlgo.__init__(self, orderManager, mdataProvider)

    def initialize(self, config):
        AbstractAlgo.initialize(self, config)

        self.tradedCurrency = config.getTradedCurrency()

        self.submitDistanceBps = config.getParam(self.SUBMIT_DISTANCE_CFG)
        self.stopProfitBps = config.getParam(self.STOP_PROFIT_CFG)
        self.stopLossBps = config.getParam(self.STOP_LOSS_CFG)
        self.orderQuantity = config.getParam(self.ORDER_QUANTITY_CFG)
        self.ordersCount = config.getParam(self.ORDERS_COUNT_CFG)
        self.allowShort = config.getParam(self.ALLOW_SHORT_CFG)
        self.allowLong = config.getParam(self.ALLOW_LONG_CFG)

        self.margin = config.getParam(self.MARGIN_CFG)
        self.postOnly = config.getParam(self.POST_ONLY_CFG)

        self.om.addListener(self)
        self.mdata.addListener(self)
        self.mdata.subscribeSymbol(self.tradedCurrency.nativeCode)

    def onNewDay(self):
        AbstractAlgo.onNewDay(self)
        logging.info("Algo initialized")

    def onTrade(self, trade):
        if trade.symbol.nativeCode == self.tradedCurrency.nativeCode:
            AbstractAlgo.onTrade(self, trade)

        if self.lastTrade is None or self.isZeroPrice(self.lastTrade.price):
            return

        self.manageOrders()

    def manageOrders(self):
        pass

    def sendLimitOrder(self, price, quantity, marginType, postOnly):
        AbstractAlgo.sendOrder(self, self.tradedCurrency.exchange, self.tradedCurrency.nativeCode, price, quantity, marginType, postOnly)

    def submitCrossingBuys(self, margin):
        self.submitBuyQuotes(-self.submitDistanceBps, margin)

    def submitCrossingSells(self, margin):
        self.submitSellQuotes(-self.submitDistanceBps, margin)

    def submitBuyQuotes(self, submitDistanceBps, margin):
        if self.isZeroQty(self.currentPosition) and self.currentBuyRisk + self.pendingBuyRisk < self.orderQuantity:
            price = self.getRoundedPrice(self.lastTrade.price * (1 - submitDistanceBps / 10000))
            quantity = self.orderQuantity

            for i in range(self.ordersCount):
                # here is a sample how the algo can overflow our allowed risk and why a second level of checks in RiskEngine would save the day
                self.sendLimitOrder(price, quantity, BasicOrderManager.MARGIN_OPEN if margin else BasicOrderManager.CASH, self.postOnly)
            self.lastBuyQuoteTime = time.time()

    def submitSellQuotes(self, submitDistanceBps, margin):
        if self.isZeroQty(self.currentPosition) and self.currentSellRisk + self.pendingSellRisk < self.orderQuantity:
            price = self.getRoundedPrice(self.lastTrade.price * (1 + submitDistanceBps / 10000))
            quantity = -self.orderQuantity

            for i in range(self.ordersCount):
                # here is a sample how the algo can overflow our allowed risk and why a second level of checks in RiskEngine would save the day
                self.sendLimitOrder(price, quantity, BasicOrderManager.MARGIN_OPEN if margin else BasicOrderManager.CASH, self.postOnly)
            self.lastSellQuoteTime = time.time()

    def submitQtyLiquidation(self, liqPrice, liqQty, margin):
        #send counterpart liquidation order on fill. No check for in flight orders
        logging.info(self.getNow() + " Submit liquidation at " + str(liqPrice) + " when market at " + str(self.lastTrade.price))
        price = self.getRoundedPrice(liqPrice * (1 + self.stopProfitBps / 10000 if liqQty > 0 else 1 - self.stopProfitBps / 10000))
        quantity = -liqQty
        self.sendLimitOrder(price, quantity, BasicOrderManager.MARGIN_CLOSE  if margin else BasicOrderManager.CASH, False)

    def submitLiquidation(self, price, margin):
        #liquidate all position at given price if no orders in flight
        if not self.isZeroQty(self.currentPosition):
            logging.info(self.getNow() + " Submit liquidation at " + str(price) + " when market at " + str(self.lastTrade.price))
            quantity = -self.currentPosition
            if self.currentPosition < 0 and self.isZeroQty(self.currentBuyRisk + self.pendingBuyRisk):
                self.sendLimitOrder(self.getRoundedPrice(price), quantity, BasicOrderManager.MARGIN_CLOSE if margin else BasicOrderManager.CASH, False)
            elif self.currentPosition > 0 and self.isZeroQty(self.currentSellRisk + self.pendingSellRisk):
                self.sendLimitOrder(self.getRoundedPrice(price), quantity, BasicOrderManager.MARGIN_CLOSE if margin else BasicOrderManager.CASH, False)

    def getRoundedPrice(self, price, tickRule=None):
        if tickRule is None:
            tickRule = self.tickRule
        return math.floor((price + tickRule / 2) / tickRule) * tickRule
