from engine.currency import Currency
from engine.trade import Trade
from binance.client import Client
from binance.websockets import BinanceSocketManager

class BinanceMdataHandler:
    EXCHANGE_ID = "binance"

    def __init__(self):
        self.listeners = []

    def start(self):
        self.client = Client("", "")

    def stop(self):
        pass

    def subscribe(self, currency):
        self.bm = BinanceSocketManager(self.client)
        self.bm.start_trade_socket(currency, self.process_message)
        self.bm.start()

    def process_message(self, data):
        trade = Trade(str(data.get("t")),
                      Currency(self.EXCHANGE_ID, data.get("s")),
                      float(data.get("p")),
                      float(data.get("q")),
                      int(data.get("T")))

        for listener in self.listeners:
            listener.onTrade(trade)

    def addListener(self, listener):
        self.listeners.append(listener)
