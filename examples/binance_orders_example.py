import logging
import time
from binance.client import Client
from binance.websockets import BinanceSocketManager


def process_message(data):
    if data["e"] == "executionReport":
        logging.info(data)

if __name__ == '__main__':
    logging.basicConfig(filename='orders_example.log', level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())

    client = Client("apiKey", "secret")
    bm = BinanceSocketManager(client)
    bm.start_user_socket(process_message)
    bm.start()

    clOrdId = "TEST-ORDER-1"
    symbol = "BTCUSDT"

    logging.info("ORDER NEW: " + clOrdId)
    order = client.create_order(
        symbol=symbol,
        newClientOrderId=clOrdId,
        side=Client.SIDE_SELL,
        type=Client.ORDER_TYPE_LIMIT,
        price=7500,
        quantity=0.002,
        timeInForce=Client.TIME_IN_FORCE_GTC)
    logging.info(order)

    orderId = order.get("orderId")
    time.sleep(5)

    client.cancel_order(
        symbol=symbol,
        orderId=int(orderId)
    )