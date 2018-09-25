import logging
import traceback
from engine.basic_order_manager import BasicOrderManager
from engine.currency import Currency
from engine.execution import Execution
from engine.exec_type import ExecType
from binance.client import Client
from binance.websockets import BinanceSocketManager

class BinanceOrdersHandler:
    EXCHANGE_ID = "binance"

    def __init__(self):
        self.listeners = []

    def start(self, apiKey, secret):
        self.client = Client(apiKey, secret)
        self.bm = BinanceSocketManager(self.client)
        self.bm.start_user_socket(self.process_message)
        self.bm.start()

    def stop(self):
        pass

    def addListener(self, listener):
        self.listeners.append(listener)

    def getExecType(self, e):
        if e == "NEW" or e == "REPLACED":
            return ExecType.NEW
        elif e == "CANCELED":
            return ExecType.CANCELED
        elif e == "REJECTED":
            return ExecType.REJECTED
        elif e == "TRADE":
            return ExecType.FILL
        elif e == "EXPIRED":
            return ExecType.EXPIRED
        else:
            return ExecType.OTHER

    def process_message(self, data):
        if data["e"] == "executionReport":
            e = Execution(data.get("t"),
                          str(data.get("i")),
                          data.get("c"),
                          self.getExecType(data.get("x")),
                          data.get("s"),
                          float(data.get("p")),
                          float(data.get("q")) * (1 if data["S"] == "BUY" else -1),
                          float(data.get("n")),
                          int(data.get("T")))

            for listener in self.listeners:
                listener.onExecution(e)


    def placeLimitOrder(self, clOrdId, symbol,
                        side, quantity, price,
                        stopPrice, marginType, postOnly):
        try:
            order = self.client.create_order(
                symbol=symbol,
                newClientOrderId=clOrdId,
                side=Client.SIDE_BUY if BasicOrderManager.isBuy(side) else Client.SIDE_SELL,
                type=Client.ORDER_TYPE_LIMIT,
                price=price,
                quantity=quantity,
                timeInForce=Client.TIME_IN_FORCE_GTC)
            return str(order.get("orderId"))
        except:
            logging.error("Failed order create for " + clOrdId)
            logging.error(traceback.format_exc())
            return None


    def cancelOrder(self, symbol, orderId):
        try:
            self.client.cancel_order(
                symbol=symbol,
                orderId=int(orderId)
            )
        except:
            logging.error("Failed canceling order for " + orderId)
            logging.error(traceback.format_exc())
