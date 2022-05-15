import unittest

from exchanges.bitmex import BitmexClient
from exchanges.binance import BinanceClient

from exchanges import binance, bitmex
from main import MainMenu
from main import *
from strategies import *
from exchanges import *
from exchanges import *

from logging import root



"""
class TestBinanceConnection(unittest.TestCase):
    def test_binance_connection(self):
        binance_public_key = "tyhjtyjdtyjdtyjdtyjdtyd456356y356y3565u7u657u4567u467u467u467uuu"
        binance_secret_key = "455345g56h56h356huki8kl689o5o567n6737g67j74j67j46873563657m7m567"
        futures = True

        connection = BinanceClient(binance_public_key, binance_secret_key, futures)

        self.assertIsInstance(connection.public_key_binance, str)
        self.assertIsInstance(connection.secret_key_binance, str)
        self.assertIsInstance(connection.testnet, bool)
        self.assertIsInstance(connection.futures, bool)
"""

class TestBitmexConnection(unittest.TestCase):
    def test_bitmex_connection(self):
        public_key_bitmex = "tyhjtyjdtyjdtyjdtyjdtyd456356y35"
        secret_key_bitmex = "455345g56h56h356huki8kl689o5o567n6737g67j74j67j46873563657m7m567"
        testnet = True

        connection = BitmexClient(public_key_bitmex, secret_key_bitmex, testnet)

        self.assertIsInstance(connection.public_key_bitmex, str)
        self.assertIsInstance(connection.secret_key_bitmex, str)
        self.assertIsInstance(connection.testnet, bool)

class TestParentStrategy(unittest.TestCase):
    def test_strategy(self):
        exchange = 'binance'
        timeframe = '1h'
        client = BitmexClient
        contract = 'binance_futures'
        balance_pct = 2000.00
        take_profit = 12.00
        stop_loss = 10.00
        strat_name = BreakoutStrategy

        new_strategy = Strategy(client, contract, exchange,
                                timeframe, balance_pct, take_profit, stop_loss, strat_name)

        self.assertIsInstance(new_strategy.exchange, str)
        self.assertIsInstance(new_strategy.timeframe, str)
        self.assertIsInstance(new_strategy.contract, str)
        self.assertIsInstance(new_strategy.balance_pct, float)
        self.assertIsInstance(new_strategy.take_profit, float)
        self.assertIsInstance(new_strategy.stop_loss, float)

class TestGuiTitle(unittest.TestCase):

    async def _start_app(self):
        self.app.mainloop()

    def setUp(self):
        self.app = Graph()
        self._start_app()

    def tearDown(self):
        self.app.destroy()

    def test_title_true(self):
        title = self.app.title()
        expected = 'TradeKing'
        self.assertEqual(title, expected)

    def test_title_false(self):
        title = self.app.title()
        expected = 'NotTradeKing'
        self.assertNotEqual(title, expected)


class TestGeometry(unittest.TestCase):

    async def _start_app(self):
        self.app.mainloop()

    def setUp(self):
        self.app = Graph()
        self._start_app()

    def tearDown(self):
        self.app.destroy()

    def test_geometry_true(self):
        result = self.app.geometry()
        expected = '1x1+0+0'
        self.assertEqual(result, expected)

    def test_geometry_false(self):
        result = self.app.geometry()
        expected = 'False'
        self.assertNotEqual(result, expected)
