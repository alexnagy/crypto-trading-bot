import sys
from connectors.binance_mdatareplay_handler import BinanceMdataReplayHandler
from engine.algo_config import AlgoConfig
from engine.simulator import Simulator
from sample_bot import SampleBot

if __name__ == '__main__':
    config = AlgoConfig(sys.argv[1])

    replayPath = config.getParam("replayPath")
    replayer = BinanceMdataReplayHandler(replayPath)

    simulator = Simulator('binance')

    mdataHandlersFactory = {
        'binance': replayer
    }
    orderHandlersFactory = {
        'binance': simulator
    }

    sampleBot = SampleBot()
    sampleBot.run(config, mdataHandlersFactory, orderHandlersFactory)

    sampleBot.engine.mdataProvider.addListener(simulator)

    replayer.replayData()
