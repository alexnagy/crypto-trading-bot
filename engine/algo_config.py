import json
from engine.currency import Currency

class AlgoConfig:
    EXCHANGE = "exchange"
    TRADED_CURRENCY = "tradedCurrency"
    API_KEY = "apiKey"
    API_SECRET = "apiSecret"

    def __init__(self, config):
        with open(config) as f:
            self.args = json.load(f)

    def getParam(self, param, default = None):
        value = self.args.get(param)
        if value is None:
            value = default
        return value

    def getTradedCurrency(self):
        return Currency(self.getParam(self.EXCHANGE), self.getParam(self.TRADED_CURRENCY))