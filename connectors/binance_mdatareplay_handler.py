import json
from engine.trade import Trade
from engine.currency import Currency


class BinanceMdataReplayHandler:
    EXCHANGE_ID = "binance"

    def __init__(self, replayPath):
        self.replayPath = replayPath
        self.listeners = []

    def start(self):
        self.reader = open(self.replayPath)

    def stop(self):
        self.reader.close()

    def subscribe(self, currency):
        pass

    def addListener(self, listener):
        self.listeners.append(listener)

    def replayData(self):
        lines = self.reader.readlines()
        for line in lines:
            self.processLine(line)

    def processLine(self, line):
        data = json.loads(line)
        trade = Trade(data.get("t"),
                      Currency(self.EXCHANGE_ID, data.get("s")),
                      data.get("p"),
                      data.get("q"),
                      data.get("T"))

        for listener in self.listeners:
            listener.onTrade(trade)
