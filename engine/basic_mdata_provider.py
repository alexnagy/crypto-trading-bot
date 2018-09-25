from engine.algo_config import AlgoConfig

class BasicMarketdataProvider:
    def __init__(self, factory):
        self.listeners = []
        self.factory = factory

    def initialize(self, config):
        self.mdataHandler = self.factory.get(config.getParam(AlgoConfig.EXCHANGE))
        self.mdataHandler.start()
        self.mdataHandler.addListener(self)

    def addListener(self, listener):
        self.listeners.append(listener)

    def subscribeSymbol(self, symbol):
        self.mdataHandler.subscribe(symbol)

    def onTrade(self, trade):
        for listener in self.listeners:
            listener.onTrade(trade)
