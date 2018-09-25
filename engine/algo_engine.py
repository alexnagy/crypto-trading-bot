import logging
from engine.basic_mdata_provider import BasicMarketdataProvider
from engine.basic_order_manager import BasicOrderManager
from engine.risk_handler import RiskHandler

class AlgoEngine:
    def __init__(self, config, mdataHandlersFactory, orderHandlersFactory, algoFactory):
        self.config = config
        self.mdataHandlersFactory = mdataHandlersFactory
        self.orderHandlersFactory = orderHandlersFactory
        self.algoFactory = algoFactory
        self.algos = []

    def start(self):
        self.startMarketData()
        self.startOM()
        self.startAlgos()

    def startMarketData(self):
        logging.info("Initializing market data")
        self.mdataProvider = BasicMarketdataProvider(self.mdataHandlersFactory)
        self.mdataProvider.initialize(self.config)

    def startOM(self):
        logging.info("Initializing OM")
        riskHandler = RiskHandler(
            BasicOrderManager(self.orderHandlersFactory)
        )
        self.mdataProvider.addListener(riskHandler)

        self.om = riskHandler
        self.om.initialize(self.config)

    def startAlgos(self):
        logging.info("Initializing algos")
        algoType = self.config.getParam("algoType")

        algo = self.algoFactory[algoType](self.om, self.mdataProvider)
        algo.initialize(self.config)
        algo.onNewDay()

        self.algos.append(algo)

