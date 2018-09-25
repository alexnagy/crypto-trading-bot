import sys
from time import sleep
from engine.algo_config import AlgoConfig
from connectors.binance_mdata_handler import BinanceMdataHandler
from connectors.binance_orders_handler import BinanceOrdersHandler
from sample_bot import SampleBot

if __name__ == '__main__':
    config = AlgoConfig(sys.argv[1])

    mdataHandlersFactory = {
        'binance': BinanceMdataHandler()
    }
    orderHandlersFactory = {
        'binance': BinanceOrdersHandler()
    }

    sampleBot = SampleBot()
    sampleBot.run(config, mdataHandlersFactory, orderHandlersFactory)

    while True:
        sleep(1)
