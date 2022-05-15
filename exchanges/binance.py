import logging
import requests
import json
import time
import hmac
import typing
import hashlib
import websocket
import collections
import threading

from urllib.parse import urlencode
from models import *
from strategies import TechnicalStrategy, BreakoutStrategy

logger = logging.getLogger()

class BinanceClient:
    def __init__(self, public_key: str, secret_key: str, testnet: bool, futures: bool):
        # All code below was followed according to doc specifications
        # Any altercations caused failed connections when performing actions
        # https://binance-docs.github.io/apidocs/futures/en

        self.futures_client = futures
        self.testnet = testnet

            #Using the API keys to connect to the Binance Futures
        self.platform = "binance_futures"
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = "wss://stream.binancefuture.com/web_s"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fstream.binance.com/web_s"

        #assign the public key
        self.public_key_binance = public_key
        #assign the secret key
        self.secret_key_binance = secret_key
        #Needed or will get "Invalid API key Error"
        self._headers = {'X-MBX-APIKEY': self.public_key_binance}

        self.contracts = self.get_cryptos()
        self.balances = self.user_balance()

        self.crypto_prices = dict() #Using Union To pass through both strategies
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        self._websocket_id = 1

        self.logs = []

        self.reconnect = True
        self.web_s: websocket.WebSocketApp
        self.ws_subscriptions = {"bookTicker": [], "aggTrade": []}
        self.websocket_connection = False


        t = threading.Thread(target=self._web_s_open)
        t.start()
        #Add A log when Web Connection is sucessfull
        logger.info("Successfully initialized: Starting TradeKing")
    #Add log to component
    def _add_log(self, response: str):
        logger.info("%s", response)
        self.logs.append({"log": response, "displayed": False})
    #Create an encrypted HMAC signature
    def _generate_signature(self, data: typing.Dict) -> str:
        # Use the HMAC-256 algorithm to create a signature
        return hmac.new(self.secret_key_binance.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()
    # Request to open a trade
    def _send_trade_request(self, request_type: str, endpoint: str, data: typing.Dict):
        # create a wrapper that handels the REST AAPI and error handling requests
        if request_type == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Error while making %s request to %s: %s", request_type, endpoint, e)
                return None

        elif request_type == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:  #This could be ude to any type of error
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
        # success
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         request_type, endpoint, response.json(), response.status_code)
            return None
    #Get the cryptos
    def get_cryptos(self) -> typing.Dict[str, ExchangeContract]:

        # Gather all the cryptos that are offered on the futures
        exchange_info = self._send_trade_request("GET", "/fapi/v1/exchangeInfo", dict())

        contracts = dict()

        if exchange_info is not None:
            #loop through all the cryptos for the exchange
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['symbol']] = ExchangeContract(contract_data, self.platform)

        return collections.OrderedDict(sorted(contracts.items()))  # Sort keys of the dictionary alphabetically
    # get the bid and ask price for a crypto
    def bid_ask_price(self, contract: ExchangeContract) -> typing.Dict[str, float]:

        gbad = dict() #Get bid ask data
        gbad['symbol'] = contract.symbol
        #Get the order book Data
        obd = self._send_trade_request("GET", "/fapi/v1/ticker/bookTicker", gbad)

        if obd is not None:
            if contract.symbol not in self.crypto_prices:  # Add the symbol to the dictionary if needed
                self.crypto_prices[contract.symbol] = {'bid': float(obd['bidPrice']), 'ask': float(obd['askPrice'])}
            else:
                self.crypto_prices[contract.symbol]['bid'] = float(obd['bidPrice'])
                self.crypto_prices[contract.symbol]['ask'] = float(obd['askPrice'])

            return self.crypto_prices[contract.symbol]
    # Get crypto Historical data
    def _historical_data(self, contract: ExchangeContract, interval: str) -> typing.List[Candle]:

        ghcd = dict()
        ghcd['symbol'] = contract.symbol
        ghcd['interval'] = interval
        ghcd['limit'] = 1000  # Tlook back candles max out at 1000


        #Binance FUtures
        raw_candles = self._send_trade_request("GET", "/fapi/v1/klines", ghcd)

        crypto_candles = []

        if raw_candles is not None:
            for c in raw_candles:
                crypto_candles.append(Candle(c, interval, self.platform))

        return crypto_candles
    # get the account balances
    def user_balance(self) -> typing.Dict[str, Balance]:

        gbd = dict() #Get Balances Data
        gbd['timestamp'] = int(time.time() * 1000)
        gbd['signature'] = self._generate_signature(gbd)

        balances = dict()

        #For binance Futures
        account_data = self._send_trade_request("GET", "/fapi/v1/account", gbd)

        if account_data is not None:
            if self.futures_client:
                for a in account_data['assets']:
                    balances[a['asset']] = Balance(a, self.platform)
            else:
                for a in account_data['balances']:
                    balances[a['asset']] = Balance(a, self.platform)

        return balances
    # Response for when starting strategy
    def _on_reponse(self, ws, response: str):

        message_data = json.loads(response) # Create a channel Update

        if "u" in message_data and "A" in message_data:
            message_data[
                'e'] = "bookTicker"  #data sturucture should be like that of binance futures

        if "e" in message_data:
            if message_data['e'] == "bookTicker": #Use binance bookTicker

                crypto = message_data['s']

                if crypto not in self.crypto_prices:
                    self.crypto_prices[crypto] = {'bid': float(message_data['b']), 'ask': float(message_data['a'])}
                else:
                    self.crypto_prices[crypto]['ask'] = float(message_data['a'])
                    self.crypto_prices[crypto]['bid'] = float(message_data['b'])
                # Profit and losses
                try:
                    for b_index, strat in self.strategies.items(): #For the body index in strategies items
                        if strat.contract.symbol == crypto:
                            for trade in strat.trades:
                                if trade.status == "open" and trade.entry_price is not None:
                                    if trade.side == "long":
                                        trade.profitloss = (self.crypto_prices[crypto]['bid'] - trade.entry_price) * trade.quantity
                                    elif trade.side == "short":
                                        trade.profitloss = (trade.entry_price - self.crypto_prices[crypto]['ask']) * trade.quantity
                except RuntimeError as e:  # Loop through a modified Dictionary
                    logger.error("Error occured with Strategies: %s", e)

            if message_data['e'] == "aggTrade": #Trade Data

                crypto = message_data['s']

                for key, strat in self.strategies.items():
                    if strat.contract.symbol == crypto:
                        res = strat.parse_trades(float(message_data['p']), float(message_data['q']),
                                                 message_data['T'])  # Updates candlesticks
                        strat.check_trade(res)
    # Create an order
    def create_crypto_trade_order(self, contract: ExchangeContract, order_type: str, quantity: float, side: str, price=None, tif=None) -> OrderStatus:

        #TIF is not needed
        # Place order.

        ctd = dict() #create crypto_trade_data
        ctd['symbol'] = contract.symbol
        ctd['side'] = side.upper()
        ctd['quantity'] = round(int(quantity / contract.lot_size) * contract.lot_size, 8)
        ctd['type'] = order_type.upper()  # MChange to upper case

        if price is not None:
            ctd['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)
            #Removing the scientific notation
            ctd['price'] = '%.*f' % (contract.price_decimals, ctd['price'])

        if tif is not None:
            ctd['timeInForce'] = tif

        ctd['timestamp'] = int(time.time() * 1000)
        ctd['signature'] = self._generate_signature(ctd)

        trade_order_status = self._send_trade_request("POST", "/fapi/v1/order", ctd)

        if trade_order_status is not None:


            trade_order_status = OrderStatus(trade_order_status, self.platform)

        return trade_order_status
    # Cancel an order
    def cancel_order(self, contract: ExchangeContract, order_id: int) -> OrderStatus:

        cod = dict() #cancel order data
        cod['orderId'] = order_id
        cod['symbol'] = contract.symbol

        cod['timestamp'] = int(time.time() * 1000)
        cod['signature'] = self._generate_signature(cod)

        trade_state = self._send_trade_request("DELETE", "/fapi/v1/order", cod)

        if trade_state is not None:
            trade_state = OrderStatus(trade_state, self.platform)

        return trade_state
    # Calculate the trade size
    def get_trade_size(self, contract: ExchangeContract, price: float, balance_pct: float):
        # logg new_log
        logger.info("Your trade size is...")

        account_amount = self.user_balance()

        if account_amount is not None:
            if contract.quote_currency in account_amount:
                account_amount = account_amount[contract.quote_currency].wallet_balance
            else:
                return None
        else:
            return None
        # calculate the trade Size
        trade_size = (account_amount * balance_pct / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)  # Removes unwanted decimals
        # log the trade size
        logger.info("Binance current %s account_amount = %s, trade size = %s", contract.quote_currency, account_amount,
                    trade_size)

        return trade_size
    # Get the status of an ongoing order
    def get_order_status(self, contract: ExchangeContract, order_id: int) -> OrderStatus:  # Must be same order as in bitmex connector

        trade_d = dict()
        trade_d['timestamp'] = int(time.time() * 1000)
        trade_d['symbol'] = contract.symbol
        trade_d['orderId'] = order_id
        trade_d['signature'] = self._generate_signature(trade_d)

        trade_order = self._send_trade_request("GET", "/fapi/v1/order", trade_d)

        if trade_order is not None:
            if not self.futures_client:
                if trade_order['status'] == "FILLED":
                    # based on previous trades this is getting the average execution prices
                    trade_order['avgPrice'] = self._get_execution_price(contract, order_id)
                else:
                    trade_order['avgPrice'] = 0

            trade_order = OrderStatus(trade_order, self.platform)

        return trade_order
    # Open the wesicket connection
    def _web_s_open(self): #Begin the websocket Connection

        # Infinite loop which will reopens the websocket connection
        # Using the WebSocketApp from _app.py
        self.web_s = websocket.WebSocketApp(self._wss_url, on_open=self._open_confirm, on_close=self._close_confirm,
                                            on_error=self._ws_connection_failure, on_message=self._on_reponse)

        while True:
            try:
                if self.reconnect:  # Reconnect unless the gui is closed by the user
                    self.web_s.run_forever()  # BLock request_type if connection is dropped
                else:
                    break
            except Exception as e:
                logger.error("Binance error in the run_forever() request_type: %s", e)
            time.sleep(20)
    # Notify that the connection was successfully opened
    def _open_confirm(self, ws):
        logger.info("Established Connection")

        self.websocket_connection = True

        # aggTrade is used for trade data

        for channel in ["bookTicker", "aggTrade"]:
            for symbol in self.ws_subscriptions[channel]:
                self.subscribe_channel([self.contracts[symbol]], channel, reconnection=True)

        if "BTCUSDT" not in self.ws_subscriptions["bookTicker"]:
            self.subscribe_channel([self.contracts["BTCUSDT"]], "bookTicker")
    # Notify the websocket has closed correctly
    def _close_confirm(self, ws, *args, **kwargs):

        # when connection closes: trigger this request_type

        logger.warning("Disconnected from Websocket")
        self.websocket_connection = False
    # Notify that there was a connection failure during the closing of the websocket
    def _ws_connection_failure(self, ws, response: str): #When there is a problem this function is triggered

        logger.error("Error while connecting: %s", response)
    # Subscribe to a channel
    def subscribe_channel(self, contracts: typing.List[ExchangeContract], channel: str, reconnection=False):

        if len(contracts) > 200: #Fail if there is more than 200 subscriptions
            logger.warning("You can only have 200 subscriptions")

        csd = dict()
        csd['request_type'] = "SUBSCRIBE"
        csd['params'] = []

        if len(contracts) == 0:
            csd['params'].append(channel)
        else:
            for contract in contracts:
                if contract.symbol not in self.ws_subscriptions[channel] or reconnection:
                    csd['params'].append(contract.symbol.lower() + "@" + channel)
                    if contract.symbol not in self.ws_subscriptions[channel]:
                        self.ws_subscriptions[channel].append(contract.symbol)

            if len(csd['params']) == 0:
                return

        csd['id'] = self._websocket_id

        try:
            #The obejct has to be made into a string
            self.web_s.send(json.dumps(csd))
            logger.info("Binance: subscribing to: %s", ','.join(csd['params']))
        except Exception as e:
            logger.error("Error subscribing to @bookTicker and @aggTrade: %s", e)

        self._websocket_id += 1


