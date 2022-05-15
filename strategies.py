import logging
from typing import *
import time

from models import *

from threading import Timer

import pandas as pd

if TYPE_CHECKING:  # Import the connector class names only for typing purpose (the classes aren't actually imported)
    from exchanges.bitmex import BitmexClient
    from exchanges.binance import BinanceClient

logger = logging.getLogger()

# TFRAME_EQUIV is used in parse_trades() to compare the last candle timestamp to the new trade timestamp
TFRAME_EQUIV = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}

class Strategy:
    def __init__(self, client: Union["BitmexClient", "BinanceClient"], contract: ExchangeContract, exchange: str,
                 timeframe: str, balance_pct: float, take_profit: float, stop_loss: float, strat_name):

        self.client = client

        self.contract = contract
        self.exchange = exchange
        self.timeframe = timeframe
        self.timeframe_equiv = TFRAME_EQUIV[timeframe] * 1000
        self.balance_pct = balance_pct
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        self.strategy_name = strat_name

        self.ongoing_position = False

        self.candles: List[Candle] = []  # candles is a list of Candle objects

        self.trades: List[Trade] = []  # trades is a list of Trade objects
        self.logs = []

    def add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})  # Append a dictionary with a log new_log

    def parse_trades(self, price: float, size: float, timestamp: int) -> str:

        # Parse new trades coming in from the websocket and update the list of Candles based on the timestamp.
        # crypto_price: The trade crypto_price
        # size: The trade size
        # timestamp: Unix timestamp in milliseconds

        timestamp_diff = int(time.time() * 1000) - timestamp  # multiply by 1000 to get miliseconds
        if timestamp_diff >= 2000:
            logger.warning("%s %s: %s milliseconds of difference between the current time and the trade time",
                           self.exchange, self.contract.symbol, timestamp_diff)

        previous_candle = self.candles[-1]

        # Same Candle

        if timestamp < previous_candle.timestamp + self.timeframe_equiv:

            previous_candle.close = price
            previous_candle.volume += size

            if price > previous_candle.high:
                previous_candle.high = price
            elif price < previous_candle.low:
                previous_candle.low = price

            # Check Take profit / Stop loss

            for trade in self.trades:
                if trade.status == "open" and trade.entry_price is not None:
                    self._check_tp_sl(trade)

            return "same_candle"

        # Missing Candle(s)

        elif timestamp >= previous_candle.timestamp + 2 * self.timeframe_equiv:

            missing_candles = int((timestamp - previous_candle.timestamp) / self.timeframe_equiv) - 1

            logger.info("%s missing %s candles for %s %s (%s %s)", self.exchange, missing_candles, self.contract.symbol,
                        self.timeframe, timestamp, previous_candle.timestamp)

            for missing in range(missing_candles):
                new_ts = previous_candle.timestamp + self.timeframe_equiv
                candle_info = {'ts': new_ts, 'open': previous_candle.close, 'high': previous_candle.close,
                               'low': previous_candle.close, 'close': previous_candle.close, 'volume': 0}
                new_candle = Candle(candle_info, self.timeframe, "parse_trade")

                self.candles.append(new_candle)

                previous_candle = new_candle

            new_ts = previous_candle.timestamp + self.timeframe_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price,
                           'volume': size}
            new_candle = Candle(candle_info, self.timeframe, "parse_trade")

            self.candles.append(new_candle)

            return "new_candle"

        # New Candle

        elif timestamp >= previous_candle.timestamp + self.timeframe_equiv:
            new_ts = previous_candle.timestamp + self.timeframe_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price,
                           'volume': size}
            new_candle = Candle(candle_info, self.timeframe, "parse_trade")

            self.candles.append(new_candle)

            logger.info("%s New candle for %s %s", self.exchange, self.contract.symbol, self.timeframe)

            return "new_candle"

    def _check_trade_order_status(self, order_id):

        # Called  after an order has been placed, continues until it is filled.

        trade_order_status = self.client.get_order_status(self.contract, order_id)

        if trade_order_status is not None:

            logger.info("%s order status: %s", self.exchange, trade_order_status.status)

            if trade_order_status.status == "filled":
                for trade in self.trades:  # Loop through the trades - it may not be the only one placed
                    if trade.entry_id == order_id:
                        trade.entry_price = trade_order_status.average_price
                        trade.quantity = trade_order_status.executed_qty
                        break
                return

        tmr = Timer(2.0,
                    lambda: self._check_trade_order_status(
                        order_id))  # Check every 2 seconds until order status is filled
        tmr.start()

    def _open_position(self, signal_result: int):

        # Open Long or Short position based on the signal result.
        # signal_result: 1 (Long) or -1 (Short)

        trade_size = self.client.get_trade_size(self.contract, self.candles[-1].close, self.balance_pct)
        if trade_size is None:
            return

        order_type = "buy" if signal_result == 1 else "sell"
        position_side = "long" if signal_result == 1 else "short"

        self.add_log(f"{position_side.capitalize()} signal on {self.contract.symbol} {self.timeframe}")

        order_state = self.client.create_crypto_trade_order(self.contract, "MARKET", trade_size, order_type)

        if order_state is not None:
            self.add_log(f"{order_type.capitalize()} order placed on {self.exchange} | Status: {order_state.status}")

            self.ongoing_position = True

            average_fill_price = None

            if order_state.status == "filled":
                average_fill_price = order_state.average_price
            else:
                tmr = Timer(2.0, lambda: self._check_trade_order_status(order_state.order_id))
                tmr.start()

            new_trade = Trade({"time": int(time.time() * 1000), "entry_price": average_fill_price,
                               "contract": self.contract, "strategy": self.strategy_name, "side": position_side,
                               "status": "open", "profitloss": 0, "quantity": order_state.executed_qty,
                               "entry_id": order_state.order_id})
            self.trades.append(new_trade)

    def _check_tp_sl(self, trade: Trade):

        # Based on the average entry crypto_price and calculates
        #If  the defined stop loss or take profit has been acheived.
        current_price = self.candles[-1].close

        stop_loss_triggered = False
        take_profit_triggered = False

        if trade.side == "short":
            if self.take_profit is not None:
                if current_price <= trade.entry_price * (1 - self.take_profit / 100):
                    take_profit_triggered = True
            if self.stop_loss is not None:
                if current_price >= trade.entry_price * (1 + self.stop_loss / 100):
                    stop_loss_triggered = True

        elif trade.side == "long":
            if self.take_profit is not None:
                if current_price >= trade.entry_price * (1 + self.take_profit / 100):
                    take_profit_triggered = True
            if self.stop_loss is not None:
                if current_price <= trade.entry_price * (1 - self.stop_loss / 100):
                    stop_loss_triggered = True

        if stop_loss_triggered or take_profit_triggered:

            self.add_log(
                f"| Current Price = {current_price} (Entry price was {trade.entry_price})"
                f"{'Stop loss' if stop_loss_triggered else 'Take profit'} for {self.contract.symbol} {self.timeframe} ")

            order_side = "SELL" if trade.side == "long" else "BUY"

            order_status = self.client.create_crypto_trade_order(self.contract, "MARKET", trade.quantity, order_side)

            if order_status is not None:
                self.add_log(f"Exit order on {self.contract.symbol} {self.timeframe} placed successfully")
                trade.status = "closed"
                self.ongoing_position = False

class BreakoutStrategy(Strategy):
    def __init__(self, client, contract: ExchangeContract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Breakout")
        # only one variable needed - The min volume
        self.min_volume = other_params['min_volume']

    def _check_signal(self) -> int:

        # Use candlesticks OHLC data to define Long or Short patterns and return a 1 for long signal and -1 for the short signal

        if self.candles[-1].close > self.candles[-2].high and self.candles[-1].volume > self.min_volume:
            return 1
        elif self.candles[-1].close < self.candles[-2].low and self.candles[-1].volume > self.min_volume:
            return -1
        else:
            return 0

    def check_trade(self, tick_type: str):

        # triggered from the websocket _on_message() methods

        if not self.ongoing_position:
            signal_result = self._check_signal()

            if signal_result in [1, -1]:
                self._open_position(signal_result)

class TechnicalStrategy(Strategy):
    def __init__(self, client, contract: ExchangeContract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Technical")


        self._ema_slow = other_params['ema_slow']
        self._ema_fast = other_params['ema_fast']
        self._rsi_length = other_params['rsi_length']
        self._ema_signal = other_params['ema_signal']

    def _rsi(self) -> float:

        # Compute the Relative Strength Index.

        close_price_list = []
        for candle in self.candles:
            close_price_list.append(candle.close)

        closes = pd.Series(close_price_list)

        # Find the difference between the row before and the current
        delta_value = closes.diff().dropna()

        down, up = delta_value.copy(), delta_value.copy()
        down[down > 0] = 0 # only negative are kept
        up[up < 0] = 0

        avg_gain = up.ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()
        avg_loss = down.abs().ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()

        rs = avg_gain / avg_loss  # Relative Strength

        rsi = 100 - 100 / (1 + rs)
        rsi = rsi.round(2)

        return rsi.iloc[-2]

    def _macd(self) -> Tuple[float, float]:

        # Compute the MACD and its Signal line.

        close_list = []
        for candle in self.candles:
            close_list.append(candle.close)  # Use only the close crypto_price of each candlestick for the calculations

        closes = pd.Series(close_list)  # Converts the close crypto_prices list to a pandas Series.

        ema_fast = closes.ewm(span=self._ema_fast).mean()  # Exponential Moving Average request_type
        ema_slow = closes.ewm(span=self._ema_slow).mean()

        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=self._ema_signal).mean()

        return macd_line.iloc[-2], macd_signal.iloc[-2]

    def _check_signal(self):

        # Compute technical indicators and compare their value to some predefined levels to know whether to go Long, Short, or do nothing.
        # 1 for a Long signal, -1 for a Short signal, 0 for no signal

        macd_line, macd_signal = self._macd()
        relative_strength_index = self._rsi()

        print(f"rsi = {relative_strength_index}, MACD signal = {macd_signal}, MACD line = {macd_line}")

        if relative_strength_index < 30 and macd_line > macd_signal:
            return 1
        elif relative_strength_index > 70 and macd_line < macd_signal:
            return -1
        else:
            return 0

    def check_trade(self, tick_type: str):

        # To be triggered from the websocket _on_message() methods.
        # Triggered only once per candlestick to avoid constantly calculating the indicators.
        # A trade can occur only if the is no open position at the moment.

        if tick_type == "new_candle" and not self.ongoing_position:
            signal_value = self._check_signal()

            if signal_value in [1, -1]:
                self._open_position(signal_value)

