import logging
from binance.client import Client
from binance.websockets import BinanceSocketManager

def process_message(data):
    logging.info(data)

if __name__ == '__main__':
    logging.basicConfig(filename='mdata_example.log', level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())

    client = Client("", "")
    bm = BinanceSocketManager(client)
    bm.start_trade_socket("BTCUSDT", process_message)
    bm.start()
