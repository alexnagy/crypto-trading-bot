import logging
import math
from engine.basic_trading_algo import BasicTradingAlgo
from engine.exec_type import ExecType
import time

class DummyAlgo(BasicTradingAlgo):

    CLORDID_PREFIX = "TEST"

    def __init__(self, orderManager, mdataProvider):
        BasicTradingAlgo.__init__(self, orderManager, mdataProvider)

    def initialize(self, config):
        BasicTradingAlgo.initialize(self, config)

    def onNewDay(self):
        BasicTradingAlgo.onNewDay(self)
        # TODO: recover executions history


    def onTrade(self, trade):
        BasicTradingAlgo.onTrade(self, trade)

        # TODO: (1) on tick up => send BUY at best_bid - 500

        # TODO: (2) on tick down and live BUY order => cancel BUY live order

    def onExecution(self, update):
        BasicTradingAlgo.onExecution(self, update)
        # TODO: on order update => cancel order

    def getClOrdIdPrefix(self):
        return self.CLORDID_PREFIX
