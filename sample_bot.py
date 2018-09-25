import logging
from engine.algo_engine import AlgoEngine
from algos.dummy_algo import DummyAlgo

class SampleBot:
    def __init__(self):
        logging.basicConfig(filename='sample_bot.log', level=logging.INFO)
        logging.getLogger().addHandler(logging.StreamHandler())

        self.algoFactory = {
            'dummy': DummyAlgo
        }

    def run(self, config, mdataHandlersFactory, orderHandlersFactory):
        self.engine = AlgoEngine(config, mdataHandlersFactory, orderHandlersFactory, self.algoFactory)
        self.engine.start()