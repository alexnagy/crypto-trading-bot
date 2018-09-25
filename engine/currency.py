class Currency:
    def __init__(self, exchange, nativeCode):
        self.exchange = exchange
        self.nativeCode = nativeCode

    @staticmethod
    def fromNativeCode(exchange, nativeCode):
        return Currency(exchange, nativeCode)

    def __str__(self):
        return "%s@%s" % (self.nativeCode, self.exchange)
