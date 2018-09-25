def signum(pos):
    return 1 if pos > 0 else (-1 if pos < 0 else 0)

class BasicPositionManager:


    def __init__(self):
        self.position = 0
        self.closedPosition = 0

        self.totalBuyQty = 0
        self.totalBuyQtyFromZero = 0
        self.totalSellQty = 0
        self.totalSellQtyFromZero = 0
        self.totalQtyFromZero = 0
        self.buyAvgPrice = 0
        self.buyAvgPriceFromZero = 0
        self.sellAvgPrice = 0
        self.sellAvgPriceFromZero = 0

        self.openMMPnlFromZero = 0
        self.maxOpenPnl = 0
        self.minOpenPnl = 0

        self.tradedNotional = 0
        self.pnl = 0
        self.realizedPnl = 0
        self.unrealizedPnl = 0
        self.gainsRelTradedBps = 0

    def markPnl(self, mtmPrice):
        self.closedPosition = min(self.totalBuyQty, -self.totalSellQty)
        self.realizedPnl = self.closedPosition * (self.sellAvgPrice - self.buyAvgPrice)
        if self.position> 0:
            self.unrealizedPnl = self.position * (mtmPrice - self.buyAvgPrice)
            self.openMMPnlFromZero = self.position * (mtmPrice - self.buyAvgPriceFromZero)
        elif self.position < 0:
            self.unrealizedPnl = self.position * (mtmPrice - self.sellAvgPrice)
            self.openMMPnlFromZero = self.position * (mtmPrice - self.sellAvgPriceFromZero)
        else:
            self.unrealizedPnl = 0
            self.openMMPnlFromZero = 0
            self.maxOpenPnl = 0
            self.minOpenPnl = 0

        self.pnl = self.realizedPnl + self.unrealizedPnl
        self.realizedPnl = self.pnl - self.openMMPnlFromZero
        self.unrealizedPnl = self.openMMPnlFromZero

        if self.unrealizedPnl > self.maxOpenPnl:
            self.maxOpenPnl = self.unrealizedPnl
        if self.unrealizedPnl < self.minOpenPnl:
            self.minOpenPnl = self.unrealizedPnl
        self.pnl = self.realizedPnl + self.unrealizedPnl

        self.gainsRelTradedBps = 0 if self.tradedNotional == 0 else self.pnl / self.tradedNotional

    def getPnl(self):
        return self.pnl

    def getRealizedPnl(self):
        return self.realizedPnl

    def getUnrealizedPnl(self):
        return self.unrealizedPnl

    def getTradedNotional(self):
        return self.tradedNotional

    def onFill(self, price, qty):
        self.tradedNotional += price * abs(qty)
        self.position += qty

        if qty > 0:
            self.buyAvgPrice = (qty * price + self.buyAvgPrice * self.totalBuyQty) / (self.totalBuyQty + qty)
            self.totalBuyQty += qty
        else:
            self.sellAvgPrice = (qty * price + self.sellAvgPrice * self.totalSellQty) /  (self.totalSellQty + qty)
            self.totalSellQty += qty

        if signum(self.position) != signum(self.position - qty):
            self.buyAvgPriceFromZero = 0
            self.totalBuyQtyFromZero = 0
            self.sellAvgPriceFromZero = 0
            self.totalSellQtyFromZero = 0
            self.totalQtyFromZero = self.position
        else:
            self.totalQtyFromZero = qty

        if self.totalQtyFromZero > 0:
            self.buyAvgPriceFromZero = (self.totalQtyFromZero * price + self.buyAvgPriceFromZero * self.totalBuyQtyFromZero) / (self.totalBuyQtyFromZero + self.totalQtyFromZero)
            self.totalBuyQtyFromZero = self.totalBuyQtyFromZero + self.totalQtyFromZero
        elif self.totalQtyFromZero < 0:
            self.sellAvgPriceFromZero = (self.totalQtyFromZero * price + self.sellAvgPriceFromZero * self.totalSellQtyFromZero) / (self.totalSellQtyFromZero + self.totalQtyFromZero)
            self.totalSellQtyFromZero = self.totalSellQtyFromZero + self.totalQtyFromZero
