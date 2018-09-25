import logging
import math
from engine.basic_trading_algo import BasicTradingAlgo
from engine.exec_type import ExecType
import time

class DirectionalSampleAlgo(BasicTradingAlgo):

    CLORDID_PREFIX = "D1"

    SIGNAL_CHECK_INTERVAL_CFG = "signalCheckIntervalSec"
    PRICE_SAMPLING_INTERVAL_CFG = "priceSamplingIntervalSec"
    VOLUME_THRESHOLD_CFG = "volumeThreshold"
    PRICE_THRESHOLD_CFG = "priceThresholdStdevs"
    SHORT_SAMPLING_INTERVAL_CFG = "shortSamplingIntervalSec"
    LONG_SAMPLING_INTERVAL_CFG = "longSamplingIntervalSec"

    MIN_SHORT_SAMPLE_ITEMS = 10
    MIN_LONG_SAMPLE_ITEMS = 30

    def __init__(self, orderManager, mdataProvider):
        BasicTradingAlgo.__init__(self, orderManager, mdataProvider)

        self.prices = []
        self.sizes = []
        self.timestamps = []

    def initialize(self, config):
        BasicTradingAlgo.initialize(self, config)

        self.signalCheckIntervalSec = config.getParam(self.SIGNAL_CHECK_INTERVAL_CFG)
        self.priceSamplingIntervalSec = config.getParam(self.PRICE_SAMPLING_INTERVAL_CFG)
        self.volumeThreshold = config.getParam(self.VOLUME_THRESHOLD_CFG)
        self.priceThresholdStdevs = config.getParam(self.PRICE_THRESHOLD_CFG)
        self.shortSamplingIntervalSec = config.getParam(self.SHORT_SAMPLING_INTERVAL_CFG)
        self.longSamplingIntervalSec = config.getParam(self.LONG_SAMPLING_INTERVAL_CFG)

    def onNewDay(self):
        BasicTradingAlgo.onNewDay(self)
        self.lastSignalCheckTime = 0


    def onTrade(self, trade):
        BasicTradingAlgo.onTrade(self, trade)

        if trade.symbol.nativeCode == self.tradedCurrency.nativeCode:
            now = trade.timestamp

            # sampling using open price as reference. could as well use close or VWAP
            lastTimestamp = 0 if len(self.timestamps) == 0 else self.timestamps[-1]
            if lastTimestamp / (1000 * self.priceSamplingIntervalSec) != now / (1000 * self.priceSamplingIntervalSec):
                self.prices.append(trade.price)
                self.sizes.append(trade.quantity)
                self.timestamps.append(now) #should use market timestamp, but this is a mock anyway
            else:
                self.sizes[-1] = self.sizes[-1] + trade.quantity

    def getTradeSignal(self):
        if self.lastTrade is None:
            return 0

        signal = 0
        now = self.lastTrade.timestamp

        if now - self.lastSignalCheckTime > 1000 * self.signalCheckIntervalSec:
            shortSampleVolume = 0
            longSampleVolume = 0
            longSampleAvgPrice = 0
            longSamplePriceMeanSumSq = 0
            shortSampleItems = 0
            longSampleItems = 0

            while len(self.timestamps) > 0 and now - self.timestamps[0] > 1000 * self.longSamplingIntervalSec:
                self.prices.pop(0)
                self.sizes.pop(0)
                self.timestamps.pop(0)

            for i in range(len(self.timestamps)):
                price = self.prices[i]
                size = self.sizes[i]
                timestamp = self.timestamps[i]

                if now - timestamp > 1000 * self.shortSamplingIntervalSec:
                    longSampleItems += 1
                    longSampleVolume += size
                    lastAvg = longSampleAvgPrice
                    longSampleAvgPrice += (price - lastAvg) / longSampleItems
                    longSamplePriceMeanSumSq += (price - lastAvg) * (price - longSampleAvgPrice)
                else:
                    shortSampleItems += 1
                    shortSampleVolume += size

            if len(self.timestamps) > 0 and \
                            self.timestamps[-1] - self.timestamps[0] >= 1000 * self.longSamplingIntervalSec / 2 and \
                            shortSampleItems > self.MIN_SHORT_SAMPLE_ITEMS and longSampleItems > self.MIN_LONG_SAMPLE_ITEMS:
                longSampleVolatility = math.sqrt(longSamplePriceMeanSumSq / (longSampleItems - 2))
                longSampleAvgVolumeNormalized = longSampleVolume * self.shortSamplingIntervalSec / self.longSamplingIntervalSec

                if shortSampleVolume > self.volumeThreshold * longSampleAvgVolumeNormalized and self.lastTrade.price > longSampleAvgPrice + self.priceThresholdStdevs * longSampleVolatility:
                    signal = 1
                elif shortSampleVolume > self.volumeThreshold * longSampleAvgVolumeNormalized and self.lastTrade.price < longSampleAvgPrice - self.priceThresholdStdevs * longSampleVolatility:
                    signal = -1

            self.lastSignalCheckTime = now

        return signal

    def onExecution(self, update):
        BasicTradingAlgo.onExecution(self, update)

        #here we can add custom algo actions on own executions
        #sample: submit liquidations as soon as we have a fill at stop profit limit (to get passive fills)
        isFill = ExecType.FILL == update.execType or ExecType.PARTIAL_FILL == update.execType
        if isFill:
            isRiskIncreasing = self.currentPosition >= 0 and update.quantity > 0 or self.currentPosition <= 0 and update.quantity < 0
            if isRiskIncreasing:
                self.submitQtyLiquidation(update.price, update.quantity, self.margin)

    def manageOrders(self):
        if self.isZeroQty(self.currentPosition):
            signal = self.getTradeSignal()
            if self.allowLong and signal > 0:
                logging.info(self.getNow() + " Signal to BUY when market at " + str(self.lastTrade.price))
                self.submitCrossingBuys(self.margin)
            if self.allowShort and signal < 0:
                logging.info(self.getNow() + " Signal to SELL when market at " + str(self.lastTrade.price))
                self.submitCrossingSells(self.margin)
        else:
            if self.currentPosition > 0 and self.pendingSellRisk == 0:
                liqPrice = self.avgTicketExecPrice * (1 - self.stopLossBps / 10000)
                if self.lastTrade.price <= liqPrice:
                    self.cancelAllOrders()
                    self.submitLiquidation(liqPrice, self.margin)
            elif self.currentPosition < 0 and self.pendingBuyRisk == 0:
                liqPrice = self.avgTicketExecPrice * (1 + self.stopLossBps / 10000)
                if self.lastTrade.price >= liqPrice:
                    self.cancelAllOrders()
                    self.submitLiquidation(liqPrice, self.margin)

    def getClOrdIdPrefix(self):
        return self.CLORDID_PREFIX
