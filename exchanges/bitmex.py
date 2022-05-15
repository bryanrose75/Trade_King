import logging
import requests
import time
import typing
import collections

from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import json

import dateutil.parser

import threading

from models import *

from strategies import TechnicalStrategy, BreakoutStrategy


logger = logging.getLogger()


class BitmexClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool):

        # All code below was followed accroding to doc specifications
        # Any altercations caused failed connections when Executing orders on the exchange
        # https://www.bitmex.com

        self.futures = True
        self.testnet = testnet
        self.platform = "bitmex"  # Just to have more homogeneous exchanges, even if self.platform is not used

        if testnet:
            self._base_url = "https://testnet.bitmex.com"
            self._wss_url = "wss://testnet.bitmex.com/realtime"
        else:
            self._base_url = "https://www.bitmex.com"
            self._wss_url = "wss://www.bitmex.com/realtime"

        self.public_key_bitmex = public_key
        self.secret_key_bitmex = secret_key

        self.ws: websocket.WebSocketApp
        self.reconnect = True

        self.contracts = self.get_cryptos()
        self.balances = self.user_balance()

        self.prices = dict()
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        self.logs = []

        t = threading.Thread(target=self._web_s_open)
        t.start()

        logger.info("Bitmex Client successfully initialized")
    # All code below was followed according to doc specifications
    # Any altercations caused failed connections when performing actions

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    def _send_trade_request(self, request_type: str, endpoint: str, data: typing.Dict):

        headers = dict()
        expires = str(int(time.time()) + 5)
        headers['api-key'] = self.public_key_bitmex
        headers['api-expires'] = expires
        headers['api-signature'] = self._generate_signature(request_type, endpoint, expires, data)

        if request_type == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Error while making %s request to %s: %s", request_type, endpoint, e)
                return None

        elif request_type == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:  # This could be ude to any type of error
                logger.error("Error making %s request to %s: %s", request_type, endpoint, e)
                return None

        elif request_type == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Error making %s request to %s: %s", request_type, endpoint, e)
                return None
        else:
            raise ValueError()

        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         request_type, endpoint, response.json(), response.status_code)
            return None

    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:

        message = method + endpoint + "?" + urlencode(data) + expires if len(data) > 0 else method + endpoint + expires
        return hmac.new(self.secret_key_bitmex.encode(), message.encode(), hashlib.sha256).hexdigest()

    def get_trade_size(self, contract: ExchangeContract, price: float, balance_pct: float):

        #Compute the trade size for the strategy module based on the percentage of the balance
        #Used to convert the amount to invest into an amount to buy/sell


        balance = self.user_balance()
        if balance is not None:
            if 'XBt' in balance:
                balance = balance['XBt'].wallet_balance
            else:
                return None
        else:
            return None

        xbt_size = balance * balance_pct / 100

        # https://www.bitmex.com/app/perpetualContractsGuide

        if contract.quanto:
            contracts_number = xbt_size / (contract.multiplier * price)
        elif contract.inverse:
            contracts_number = xbt_size / (contract.multiplier / price)
        else:
            contracts_number = xbt_size / (contract.multiplier * price)

        logger.info("Bitmex current XBT balance = %s, contracts number = %s", balance, contracts_number)

        return int(contracts_number)

    def user_balance(self) -> typing.Dict[str, Balance]:
        dbd = dict() #Get balance Data
        dbd['currency'] = "all"

        balances = dict()

        margin_data = self._send_trade_request("GET", "/api/v1/user/margin", dbd)

        if margin_data is not None:
            for a in margin_data:
                balances[a['currency']] = Balance(a, "bitmex")

        return balances

    def get_cryptos(self) -> typing.Dict[str, ExchangeContract]:

        instruments = self._send_trade_request("GET", "/api/v1/instrument/active", dict())

        contracts = dict()

        if instruments is not None:
            for s in instruments:
                contracts[s['symbol']] = ExchangeContract(s, "bitmex")

        return collections.OrderedDict(sorted(contracts.items()))  # Sort keys of the dictionary alphabetically

    def _historical_data(self, contract: ExchangeContract, timeframe: str) -> typing.List[Candle]:
        ghcd = dict() #get historical candle data

        ghcd['symbol'] = contract.symbol
        ghcd['partial'] = True
        ghcd['binSize'] = timeframe
        ghcd['count'] = 500
        ghcd['reverse'] = True

        raw_candles = self._send_trade_request("GET", "/api/v1/trade/bucketed", ghcd)

        candles = []

        if raw_candles is not None:
            for c in reversed(raw_candles):
                if c['open'] is None or c['close'] is None:  # Some candles returned by Bitmex miss data
                    continue
                candles.append(Candle(c, timeframe, "bitmex"))

        return candles

    def create_crypto_trade_order(self, contract: ExchangeContract, order_type: str, quantity: int, side: str, price=None, tif=None) -> OrderStatus:
        pod = dict() # Place order data

        pod['symbol'] = contract.symbol
        pod['side'] = side.capitalize()
        pod['orderQty'] = round(quantity / contract.lot_size) * contract.lot_size
        pod['ordType'] = order_type.capitalize()

        if price is not None:
            pod['crypto_price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)

        if tif is not None:
            pod['timeInForce'] = tif

        order_status = self._send_trade_request("POST", "/api/v1/order", pod)

        if order_status is not None:
            order_status = OrderStatus(order_status, "bitmex")

        return order_status

    def get_order_status(self, contract: ExchangeContract, order_id: str) -> OrderStatus:  #Must be same order as in binance connector

        gosd = dict()
        gosd['symbol'] = contract.symbol
        gosd['reverse'] = True

        order_status = self._send_trade_request("GET", "/api/v1/order", gosd)

        if order_status is not None:
            for order in order_status:
                if order['orderID'] == order_id:
                    return OrderStatus(order, "bitmex")

    def cancel_order(self, order_id: str) -> OrderStatus:
        cod = dict() #cancel order data
        cod['orderID'] = order_id

        order_status = self._send_trade_request("DELETE", "/api/v1/order", cod)

        if order_status is not None:
            order_status = OrderStatus(order_status[0], "bitmex")

        return order_status

    def _web_s_open(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._open_confirm, on_close=self._close_confirm,
                                         on_error=self._ws_connection_failure, on_message=self._on_reponse)

        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever()
                else:
                    break
            except Exception as e:
                logger.error("Error: request %s", e)
            time.sleep(2)

    def _open_confirm(self, ws):
        logger.info("Bitmex connection opened")

        self.subscribe_channel("instrument")

        self.subscribe_channel("trade")

    def _close_confirm(self, ws, *args, **kwargs):
        logger.warning("Bitmex Websocket connection closed")

    def _on_reponse(self, ws, msg: str):

        omd = json.loads(msg)#On message Data

        if "table" in omd:
            if omd['table'] == "instrument":

                for d in omd['data']:

                    bx_symbol = d['symbol']

                    if bx_symbol not in self.prices:
                        self.prices[bx_symbol] = {'bid': None, 'ask': None}

                    if 'bidPrice' in d:
                        self.prices[bx_symbol]['bid'] = d['bidPrice']
                    if 'askPrice' in d:
                        self.prices[bx_symbol]['ask'] = d['askPrice']

                    # PNL Calculation

                    try:
                        for b_index, bx_strategy in self.strategies.items():
                            if bx_strategy.contract.symbol == bx_symbol:
                                for trade in bx_strategy.trades:
                                    if trade.status == "open" and trade.entry_price is not None:

                                        if trade.side == "long":
                                            price = self.prices[bx_symbol]['bid']
                                        else:
                                            price = self.prices[bx_symbol]['ask']
                                        multiplier = trade.contract.multiplier

                                        if trade.contract.inverse:
                                            if trade.side == "long":
                                                trade.profitloss = (1 / trade.entry_price - 1 / price) * multiplier * trade.quantity
                                            elif trade.side == "short":
                                                trade.profitloss = (1 / price - 1 / trade.entry_price) * multiplier * trade.quantity
                                        else:
                                            if trade.side == "long":
                                                trade.profitloss = (price - trade.entry_price) * multiplier * trade.quantity
                                            elif trade.side == "short":
                                                trade.profitloss = (trade.entry_price - price) * multiplier * trade.quantity
                    except RuntimeError as e:
                        logger.error("Error with strategies: %s", e)

            if omd['table'] == "trade":

                for d in omd['data']:

                    bx_symbol = d['symbol']

                    ts = int(dateutil.parser.isoparse(d['timestamp']).timestamp() * 1000)

                    for key, bx_strategy in self.strategies.items():
                        if bx_strategy.contract.symbol == bx_symbol:
                            res = bx_strategy.parse_trades(float(d['crypto_price']), float(d['size']), ts)
                            bx_strategy.check_trade(res)

    def _ws_connection_failure(self, ws, msg: str):
        logger.error("Bitmex connection error: %s", msg)

    def subscribe_channel(self, topic: str):
        scd = dict() #subscribe channel data
        scd['op'] = "subscribe"
        scd['args'] = []
        scd['args'].append(topic)

        try:
            self.ws.send(json.dumps(scd))
        except Exception as e:
            logger.error("Error subscribing to %s: %s", topic, e)














