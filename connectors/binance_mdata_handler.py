from engine.currency import Currency
from engine.trade import Trade
from binance.client import Client
from binance.websockets import BinanceSocketManager

class BinanceMdataHandler:
    EXCHANGE_ID = "binance"

    def __init__(self):
        self.listeners = []

    def start(self):
        # TODO: start market data handler
        pass

    def stop(self):
        # TODO: stop market data handler
        pass

    def subscribe(self, currency):
        # TODO: write market data handling code
        pass

    def addListener(self, listener):
        self.listeners.append(listener)
