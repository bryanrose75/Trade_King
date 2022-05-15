import re
import tkinter as tk
import webbrowser

from tkinter.messagebox import askquestion
import logging
import json
from tkinter.ttk import Style

from exchanges.bitmex import BitmexClient
from exchanges.binance import BinanceClient


from gui.process_log import ProcessLog
from gui.crypto_watchlist import CryptoLive
from gui.user_trades import UserTrades
from gui.strategy import TradingStrategy

import matplotlib
from matplotlib import pyplot as plt

import datetime
import tkmacosx as tkmac

import requests

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

matplotlib.use("TkAgg")

from gui.styling import *

import pandas as pd
import numpy as np

global crypto_name

info_log = logging.getLogger()

from logging import root

from tkinter import ttk, W, E, FALSE, N, S
from tkinter import messagebox


# TradeKingRoot for the Login Menu
class MainMenu(tk.Tk):

    def __init__(self, root):
        # check current system
        # check_current_system()

        # Set up main application window
        root.title("TradeKing")  # Page header title
        #root.config(background=backgound_color)

        s = Style()
        s.configure('My.TFrame', background=backgound_color)

        # Create content frame (parent window)
        mainframe = ttk.Frame(root, style='My.TFrame')
        mainframe['padding'] = 5
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Create Menu functionality
        root.option_add('*tearOff',
                        FALSE)  # Essential. Each menu will be broken otherwise

        # Create header frame (child of mainframe window)
        header_frame = ttk.Frame(mainframe, style='My.TFrame')
        header_frame['padding'] = 5  # Add 5 to padding for all directions
        header_frame['borderwidth'] = 2
        header_frame['relief'] = 'sunken'

        # Title / Info Label
        ttk.Label(header_frame, text="Welcome to TradeKing!\n").grid(column=0, row=0)
        ttk.Label(header_frame, text="To get started, please enter an API key for Binance or Bitmax.\n").grid(column=0,
                                                                                                              row=1)
        ttk.Label(header_frame, text="**Ensure API keys are for the Testnet platforms.**\n").grid(column=0,
                                                                                                              row=2)
        ttk.Label(header_frame, text="For information on how to retreive your API key please\n").grid(column=0, row=3)

        # Button to display Binance API Key retreival help
        ttk.Button(header_frame, text="Click here for Binance!", command=_open_browser_binance_keys).grid(column=0, row=4,
                                                                                                  sticky=W)
        ttk.Button(header_frame, text="Click here for Bitmax!", command=_open_browser_bitmax_keys).grid(column=0, row=4,
                                                                                              sticky=E)

        # Create form frame (child of mainframe window)
        form_frame = ttk.Frame(mainframe, style='My.TFrame')
        form_frame['padding'] = 5
        form_frame['borderwidth'] = 2
        form_frame['relief'] = 'sunken'

        # Create entry widget for public key
        self.public_key = tk.StringVar()
        public_key_entry = ttk.Entry(form_frame, width=40, textvariable=self.public_key)
        public_key_entry.grid(column=0, row=1, sticky=(W, E))
        self.public_key_val = tk.StringVar()  # Variable used as output test - can be removed later

        # Create entry widget for secret key
        self.secret_key = tk.StringVar()
        secret_key_entry = ttk.Entry(form_frame, width=40, textvariable=self.secret_key, show="*")
        secret_key_entry.grid(column=0, row=3, sticky=(W, E))
        self.secret_key_val = tk.StringVar()  # Variable used as output test - can be removed later

        # Display labels for key input
        ttk.Label(form_frame, text="Enter Public Key: ").grid(column=0, row=0)
        ttk.Label(form_frame, text="Enter Secret Key: ").grid(column=0, row=2)

        # Create button frame (child of mainframe window)
        button_frame = ttk.Frame(mainframe, style='My.TFrame')
        button_frame['padding'] = 5
        button_frame['borderwidth'] = 2
        button_frame['relief'] = 'sunken'


        # Button to validate keys
        ttk.Button(button_frame, text="GO!", command=self.validate).grid(column=0, row=0, sticky=W)

        # Display key values
        ttk.Label(form_frame, textvariable=self.public_key_val).grid(column=0, row=4, sticky=(W, E))  # Public
        ttk.Label(form_frame, textvariable=self.secret_key_val).grid(column=0, row=5, sticky=(W, E))  # Secret

        # Tidy all widgets - Add padding to each child (widget) attached to parent (mainframe)
        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)


        public_key_entry.focus()  # Set curser to start on this widget
        root.bind("<Return>", self.validate)  # Call validate routine if button press

        # Button for closing
        ttk.Button(button_frame, text="Exit", command=close_app).grid(column=0, row=1)



    def validate(self):
        """
        Notes:
        > new function to be added for actual API verification call

        Regex for from validation:
        > /^[a-fA-F0-9-]*$/gm
        """
        #global pk_val, sk_val
        #new_log = ''  # Using this in case of incorrect form input
        if len(self.public_key.get()) == 0 or self.public_key.get() is None:
            message = 'Public Key cannot be empty!'
            print(message)
        elif len(self.secret_key.get()) == 0 or self.public_key.get() is None:
            message = 'Secret Key cannot be empty!'
            print(message)
        else:
            try:
                #Connect to Binance
                if re.match('^[a-zA-Z\d-]*$', self.public_key.get()):
                    pk_val = self.public_key.get()
                    print("> Public Key Entered: [", pk_val, "]")
                    self.public_key_val.set(pk_val)

                    if re.match('^[a-zA-Z\d-]*$', self.secret_key.get()):
                        sk_val = self.secret_key.get()
                        print("> Secret Key Entered: [", sk_val, "]")
                        self.secret_key_val.set(sk_val)
                        message = 'Success'

                        # Check running a new window
                        root.destroy()

                        secret_key = sk_val
                        public_key = pk_val

                        go_binance(secret_key, public_key)

                    else:
                        message = 'Invalid Secret Key Entered!'

                #Connect to Bitmex
                if re.match('^[a-zA-Z\d]+$', self.public_key.get()):
                    pk_val = self.public_key.get()
                    print("> Public Key Entered: [", pk_val, "]")
                    self.public_key_val.set(pk_val)

                    if re.match('^[a-zA-Z\d_-]+$', self.secret_key.get()):
                        sk_val = self.secret_key.get()
                        print("> Secret Key Entered: [", sk_val, "]")
                        self.secret_key_val.set(sk_val)
                        message = 'Success'

                        # Check running a new window
                        root.destroy()

                        secret_key = sk_val
                        public_key = pk_val

                        go_bitmex(secret_key, public_key)

                    else:
                        message = 'Invalid Secret Key Entered!'

                #Invalid Regex
                else:
                    message = 'Invalid Public Key Format Entered!'
                if any(ch.isspace() for ch in self.public_key.get()):
                    message = 'Public Key cannot have spaces'
                    print(message)
                if any(ch.isspace() for ch in self.secret_key.get()):
                    message = 'Secret Key cannot have spaces'
                    print(message)
            except Exception as e:
                messagebox.showerror('error', e.__cause__)
        # Only display new_log box on failure
        if message != '' and message != 'Success':
            messagebox.showinfo('new_log', message)

# TradeKingRoot for the Trading Bot
class TradeKingRoot(tk.Tk):
    global graph_root

    def __init__(self, binance: BinanceClient, bitmex: BitmexClient):
        super().__init__()

        self.binance = binance
        self.bitmex = bitmex

        self.title("TradeKing")
        self.protocol("WM_DELETE_WINDOW", self._termination)

        self.configure(bg=backgound_color)

        # Creating all the menus
        # Menus are useful to have more available space on the windows without having too many buttons

        self.tradeking_menu_main = tk.Menu(self)
        self.configure(menu=self.tradeking_menu_main)

        self.save_workspace = tk.Menu(self.tradeking_menu_main, tearoff=False)
        self.tradeking_menu_main.add_cascade(label="Workspace", menu=self.save_workspace)
        self.save_workspace.add_command(label="Save workspace", command=self._save_workspace)

        self.tradeking_menu_main.add_cascade(label="Crypto Graphs", menu=self.save_workspace)
        self.save_workspace.add_command(label="Enter Graphs Page", command=self._open_graphs)

        # splitting the Trade king menu into two frames

        self._cryptolive_processlog = tk.Frame(self, bg=backgound_color)
        self._cryptolive_processlog.pack(side=tk.LEFT)

        self._strategy_tradeswatch = tk.Frame(self, bg=backgound_color)
        self._strategy_tradeswatch.pack(side=tk.LEFT)

        # The trades and strategy are placed in the right frame and the crypto lives and process log are placed on the left

        self._crypto_live = CryptoLive(self.binance.contracts, self.bitmex.contracts, self._cryptolive_processlog, bg=backgound_color)
        self._crypto_live.pack(side=tk.TOP, padx=10)

        self._process_log = ProcessLog(self._cryptolive_processlog, bg=backgound_color)
        self._process_log.pack(side=tk.TOP, pady=15)  # add spacing

        self._trading_strategy = TradingStrategy(self, self.binance, self.bitmex, self._strategy_tradeswatch, bg=backgound_color)
        self._trading_strategy.pack(side=tk.TOP, pady=15)

        self._user_trades = UserTrades(self._strategy_tradeswatch, bg=backgound_color)
        self._user_trades.pack(side=tk.TOP, pady=15)

        self.gui_update()  # Starts the infinite gui update loop



    def gui_update(self):

        #thread safe as it runs within the mainloop() thread
        #Tk elements from another thread such as the websocket
        #called every 1500 seconds

        # Logs

        for log in self.bitmex.logs:
            if not log['displayed']:
                self._process_log.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log['displayed']:
                self._process_log.add_log(log['log'])
                log['displayed'] = True

        # Trades and Logs

        for client in [self.binance, self.bitmex]:

            try:  # try...except statement to handle the case when a dictionary is updated during the following loops

                for b_index, strat in client.strategies.items():
                    for log in strat.logs:
                        if not log['displayed']:
                            self._process_log.add_log(log['log'])
                            log['displayed'] = True

                    # Update the Trades component (add a new trade, change status/PNL)

                    for trade in strat.trades:
                        if trade.time not in self._user_trades.trades_col['symbol']:
                            self._user_trades.add_trade(trade)

                        if "binance" in trade.contract.exchange:
                            precision = trade.contract.price_decimals
                        else:
                            precision = 8  # The Bitmex PNL is always is BTC, thus 8 decimals

                        pnl_str = "{0:.{prec}f}".format(trade.profitloss, prec=precision)
                        self._user_trades.trades_col['pnl_var'][trade.time].set(pnl_str)
                        self._user_trades.trades_col['status_var'][trade.time].set(trade.status.capitalize())
                        self._user_trades.trades_col['size_var'][trade.time].set(trade.quantity)

            except RuntimeError as e:
                info_log.error("Error while looping through strategies dictionary: %s", e)

        # CryptoLive crypto_prices

        try:
            for key, value in self._crypto_live.body_widgets['symbol'].items():

                crypto = self._crypto_live.body_widgets['symbol'][key].cget("text")
                connected_exchange = self._crypto_live.body_widgets['exchange'][key].cget("text")

                if connected_exchange == "Binance":
                    if crypto not in self.binance.contracts:
                        continue

                    if crypto not in self.binance.ws_subscriptions["bookTicker"] and self.binance.websocket_connection:
                        self.binance.subscribe_channel([self.binance.contracts[crypto]], "bookTicker")

                    if crypto not in self.binance.crypto_prices:
                        self.binance.bid_ask_price(self.binance.contracts[crypto])
                        continue

                    precision = self.binance.contracts[crypto].price_decimals

                    prices = self.binance.crypto_prices[crypto]

                elif connected_exchange == "Bitmex":

                    if crypto not in self.bitmex.prices:
                        continue

                    if crypto not in self.bitmex.contracts:
                        continue

                    precision = self.bitmex.contracts[crypto].price_decimals

                    prices = self.bitmex.prices[crypto]

                else:
                    continue

                if prices['bid'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['bid'], prec=precision)
                    self._crypto_live.body_widgets['bid_var'][key].set(price_str)
                if prices['ask'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['ask'], prec=precision)
                    self._crypto_live.body_widgets['ask_var'][key].set(price_str)

        except RuntimeError as e:
            info_log.error("Error: watchlist dictionary loop failed: %s", e)

        self.after(1500, self.gui_update)

    def _open_graphs(self):
        self.binance.reconnect = False
        self.bitmex.reconnect = False # during the start there is an infinite loop that needs to be avoided
        self.binance.web_s.close()
        self.bitmex.ws.close()


        #secret_key_binance = sk

        trading_bot_root.destroy()

        open_graph()

    def _save_workspace(self):


        # CryptoLive

        crypto_watch = []

        for key, value in self._crypto_live.body_widgets['symbol'].items():
            crypto = value.cget("text")
            exchange = self._crypto_live.body_widgets['exchange'][key].cget("text")

            crypto_watch.append((crypto, exchange,))

        self._crypto_live.db.save("watchlist", crypto_watch)

        # Save the strategies

        save_strat = []

        strat_widgets = self._trading_strategy.body_widgets

        for body_i in strat_widgets[
            'contract']:  # All columns are looped

            strategy_type = strat_widgets['strategy_type_var'][body_i].get()
            crypto_contract = strat_widgets['contract_var'][body_i].get()
            tf = strat_widgets['timeframe_var'][body_i].get()
            bal_percentage = strat_widgets['balance_pct'][body_i].get()
            tp = strat_widgets['tp'][body_i].get()
            sl = strat_widgets['stop_loss'][body_i].get()

            # Extra parameters are all saved in one column as a JSON string because they change based on the strategy

            extra_params = dict()

            for param in self._trading_strategy.extra_params[strategy_type]:
                code_name = param['code_name']

                extra_params[code_name] = self._trading_strategy.additional_parameters[body_i][code_name]

            save_strat.append((strategy_type, crypto_contract, tf, bal_percentage, tp, sl,
                               json.dumps(extra_params),))

        self._trading_strategy.db.save("strategies", save_strat)

        self._process_log.add_log("Workspace saved")

    def _termination(self):

        # Triggered when the user click on the Close button of the gui.
        # This lets you have control over what's happening just before closing the gui like closing websocket connections

        result = askquestion("Confirmation", "Do you really want to exit TradeKing?")
        if result == "yes":
            self.binance.reconnect = False  # Avoids the infinite reconnect loop in _start_ws()
            self.bitmex.reconnect = False
            self.binance.web_s.close()
            self.bitmex.ws.close()

            self.destroy()  # Destroys the UI and terminates the program as no other thread is running

# Root for the Trading Graphs
class Graph(tk.Tk):
    global crypto_name
    global destroy
    global crypto_ids
    global canvas_2
    global Comparelabel

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title("TradeKing")
        self.protocol("WM_DELETE_WINDOW", self._ask_before_close)

        # Create the menu, sub menu and menu commands
        # You can use the menu when you don't want to overload the interface with too many buttons

        def get_crypto_name():
            return str(crypto_variable.get())

        def get_currency():
            return str(currency_variable.get())

        def get_lookback():
            return str(lookback_variable.get())

        def get_interval():
            return str(interval_variable.get())

        # retreive the available cryptos
        def available_crypto():
            url = f'https://api.coingecko.com/api/v3/coins'
            response = requests.get(url)
            data = response.json()

            crypto_ids = []

            for asset in data: crypto_ids.append(asset['id'])

            return crypto_ids

        # retireve the chart data for any currency and return the dataframe

        def get_market_chart(coin_id, vs_currency, days, interval):
            # coin_id = get_crypto_name
            crypto_ids = available_crypto()

            if coin_id in crypto_ids:
                url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
                payload = {'vs_currency': vs_currency, 'days': days, 'interval': interval}
                response = requests.get(url, params=payload)
                data = response.json()

                timestamp_list, price_list = [], []

                # Aggregates the data in a for-loop
                for price in data['crypto_prices']:
                    timestamp_list.append(datetime.datetime.fromtimestamp(price[0] / 1000))
                    price_list.append(price[1])

                # clean the data with pandas
                raw_data = {
                    'timestamp': timestamp_list,
                    'price': price_list
                }

                df = pd.DataFrame(raw_data)
                return (df)

                price_array = df["price"].to_numpy()
            else:
                # Incase the user enters a crypto that doesnt exist
                print('The Crypto that you have selected is not available, please choose one from the following list:')
                # print(crypto_ids)

        crypto_user_choice = ", ".join(repr(e) for e in available_crypto())
        print(crypto_user_choice)

        IntroLabel = tk.Label(self, text=f"Choose the Parameters for the Crypto Graph:", font=LARGE_FONT2,
                              bg=backgound_color, fg=foreground_color)
        IntroLabel.pack(pady=20, padx=20)
        # Get The Users Crypto
        crypto_variable = tk.StringVar(self)
        crypto_variable.set("Crypto")  # default value
        crypto_variable_OM = tk.OptionMenu(self, crypto_variable, 'bitcoin', 'ethereum', 'tether', 'binancecoin',
                                           'usd-coin', 'solana', 'ripple',
                                           'terra-luna', 'cardano', 'avalanche-2', 'polkadot', 'dogecoin', 'terrausd',
                                           'binance-usd', 'shiba-inu',
                                           'wrapped-bitcoin', 'staked-ether', 'crypto-com-chain', 'near',
                                           'matic-network',
                                           'dai', 'bonded-luna',
                                           'litecoin', 'cosmos', 'tron', 'chainlink', 'bitcoin-cash', 'apecoin',
                                           'leo-token', 'ftx-token', 'okb',
                                           'stellar', 'algorand', 'ethereum-classic', 'monero', 'uniswap', 'vechain',
                                           'hedera-hashgraph', 'filecoin',
                                           'internet-computer', 'elrond-erd-2', 'axie-infinity', 'the-sandbox',
                                           'decentraland', 'magic-internet-money',
                                           'compound-ether', 'theta-token', 'frax', 'fantom', 'tezos')
        crypto_variable_OM.pack()

        # Get the users currency
        currency_variable = tk.StringVar(self)
        currency_variable.set("Currency")  # default value

        currency_variable_OM = tk.OptionMenu(self, currency_variable, 'usd', 'eur')

        # currency_variable_OM["highlightthickness"]=0
        currency_variable_OM.pack()

        # Get the users lookback days
        lookback_variable = tk.StringVar(self)
        lookback_variable.set("Lookback")  # default value
        lookback_variable_OM = tk.OptionMenu(self, lookback_variable, '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                                             '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22',
                                             '23',
                                             '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35',
                                             '36',
                                             '37', '38', '39', '40')
        lookback_variable_OM.pack()

        # Get the users interval
        interval_variable = tk.StringVar(self)
        interval_variable.set("Interval")  # default value
        interval_variable_OM = tk.OptionMenu(self, interval_variable, 'hourly', 'daily')
        interval_variable_OM.pack()

        # Alternativly a combobox could be used as a dropdown
        """
        combobox_variable = tk.StringVar()
        combobox_variable.set("Choose a Crypto....")
        crypto_combobox = ttk.Combobox(self, textvariable=combobox_variable)

        crypto_combobox['values'] = ('bitcoin', 'ethereum', 'tether', 'binancecoin', 'usd-coin', 'solana', 'ripple',
                       'terra-luna', 'cardano', 'avalanche-2', 'polkadot', 'dogecoin', 'terrausd', 'binance-usd', 'shiba-inu',
                       'wrapped-bitcoin', 'staked-ether', 'crypto-com-chain', 'near', 'matic-network', 'dai', 'bonded-luna',
                       'litecoin', 'cosmos', 'tron', 'chainlink', 'bitcoin-cash', 'apecoin', 'leo-token', 'ftx-token', 'okb',
                       'stellar', 'algorand', 'ethereum-classic', 'monero', 'uniswap', 'vechain', 'hedera-hashgraph', 'filecoin',
                       'internet-computer', 'elrond-erd-2', 'axie-infinity', 'the-sandbox', 'decentraland', 'magic-internet-money',
                       'compound-ether', 'theta-token', 'frax', 'fantom', 'tezos')



        crypto_combobox.pack()
        """

        def generate_graph():

            # get the variables from the combobox and drop down menu

            message = ''  # Using this in case of incorrect form input
            if get_crypto_name() == "Crypto":

                message = 'Crypto not set!'
                print(message)
            elif get_currency() == "Currency":

                message = 'Currency not set!'
                print(message)
            elif get_lookback() == "Lookback":
                message = 'Lookback not set!'
                print(message)
            elif get_interval() == "Interval":
                message = 'Interval not set!'
                print(message)

            else:

                label = tk.Label(self, text=f"{get_crypto_name()} Graph", font=LARGE_FONT2, bg=backgound_color,
                                 fg=foreground_color)
                label.pack(pady=10, padx=10)

                f = Figure(figsize=(12, 5), dpi=100)
                a = f.add_subplot(111)

                coin_id = get_crypto_name()
                vs_currency = get_currency()
                days = get_lookback()
                interval = get_interval()

                market_info = get_market_chart(coin_id, vs_currency, days, interval)

                priceArray1 = np.array(market_info.price)
                timeStampArray1 = np.array(market_info.timestamp)

                a.set_xlabel('Timeline')
                a.set_ylabel(f"{coin_id} Price Range")
                a.plot(timeStampArray1, priceArray1, color='#4285F4')
                plt.show()

                canvas = FigureCanvasTkAgg(f, self)
                canvas.draw()
                canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

                lookback_variable_OM.pack_forget()
                currency_variable_OM.pack_forget()
                crypto_variable_OM.pack_forget()
                interval_variable_OM.pack_forget()
                IntroLabel.pack_forget()

                def add_graph():

                    message = ''  # Using this in case of incorrect form input
                    if get_crypto_name() == "Add another Crypto":
                        message = 'New Crypto not set!'
                        print(message)

                    else:
                        canvas._tkcanvas.destroy()
                        label.destroy()
                        ChooseAnotherCryproLabel.pack_forget()
                        reset_button.pack_forget()

                        coin_id2 = get_crypto_name()
                        market_info_2nd_coin = get_market_chart(coin_id2, vs_currency, days, interval)
                        priceArray2 = np.array(market_info_2nd_coin.price)

                        Comparelabel = tk.Label(self, text=f"{coin_id} vs {coin_id2} Graph", font=LARGE_FONT2,
                                                bg=backgound_color, fg=foreground_color)
                        Comparelabel.pack(pady=10, padx=10)

                        # create two axes
                        # Create the figure for the second graph
                        f = Figure(figsize=(12, 5), dpi=100)
                        ax1 = f.add_subplot(111)

                        color = 'tab:red'
                        ax1.set_xlabel('Timeline')
                        ax1.set_ylabel(f"{coin_id} Price Range", color=color)
                        ax1.plot(timeStampArray1, priceArray1, color=color)
                        ax1.tick_params(axis='y', labelcolor=color)

                        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

                        color = 'tab:blue'
                        ax2.set_ylabel(f"{coin_id2} Price Range", color=color)  # already handled the x-label with ax1
                        ax2.plot(timeStampArray1, priceArray2, color=color)
                        ax2.tick_params(axis='y', labelcolor=color)
                        plt.show()

                        canvas_2 = FigureCanvasTkAgg(f, self)
                        canvas_2.draw()
                        canvas_2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

                        # toolbar2 = NavigationToolbar2Tk(canvas_2, self)
                        # toolbar2.update()
                        canvas_2._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

                        show_graph_button.pack_forget()
                        crypto_variable_OM.pack_forget()

                        def destroy_2():
                            canvas_2._tkcanvas.destroy()
                            reset_button2.destroy()
                            label.destroy()
                            Comparelabel.destroy()
                            # toolbar2.destroy()
                            IntroLabel.pack()

                            crypto_variable_OM.pack()
                            currency_variable_OM.pack()
                            lookback_variable_OM.pack()
                            interval_variable_OM.pack()
                            show_graph_button.pack()

                            lookback_variable.set("Lookback")
                            currency_variable.set("Currency")
                            crypto_variable.set("Crypto")
                            interval_variable.set("Interval")
                            compare_button.pack_forget()

                        reset_button2 = tkmac.Button(text="Reset", command=destroy_2, bg='darkred', fg=foreground_color,
                                                     height=20, borderless=True,
                                                     padx=25)
                        reset_button2.pack(pady=15, padx=15)

                        compare_button.pack_forget()
                    if message != '' and message != 'Success':
                        messagebox.showinfo('new_log', message)

                compare_button = tkmac.Button(text="Apply Crypto to Graph", command=add_graph, bg='#35b9df',
                                              fg=foreground_color, borderless=True,
                                              padx=10)
                ChooseAnotherCryproLabel = tk.Label(self, text=f"Compare another Crypto with {coin_id}",
                                                    font=LARGE_FONT, bg=backgound_color, fg=foreground_color)
                ChooseAnotherCryproLabel.pack(pady=10, padx=10)

                crypto_variable_OM.pack(pady=5, padx=5)
                crypto_variable.set("Add another Crypto")
                compare_button.pack()

                # Button to rest the graphs
                def destroy():
                    canvas._tkcanvas.destroy()
                    reset_button.destroy()
                    label.destroy()
                    Comparelabel.destroy()
                    # toolbar.destroy()
                    IntroLabel.pack()
                    show_graph_button.pack()
                    currency_variable_OM.pack()
                    lookback_variable_OM.pack()
                    interval_variable_OM.pack()
                    lookback_variable.set("Lookback")
                    currency_variable.set("Currency")
                    crypto_variable.set("Crypto")
                    interval_variable.set("Interval")
                    compare_button.pack_forget()

                reset_button = tkmac.Button(text="Reset", command=destroy, bg='darkred', fg=foreground_color, height=20,
                                            padx=25, borderless=True)
                reset_button.pack(pady=15, padx=15)

                show_graph_button.pack_forget()
                # Only display new_log box on failure
            if message != '' and message != 'Success':
                messagebox.showinfo('new_log', message)

        show_graph_button = tkmac.Button(text="Show Graph", command=generate_graph, bg='#35b9df', fg=foreground_color,
                                         height=20, padx=25, borderless=True)
        show_graph_button.pack(pady=15, padx=15)

        self.main_menu = tk.Menu(self)
        self.configure(menu=self.main_menu)

        self.workspace_menu = tk.Menu(self.main_menu, tearoff=False)

        self.main_menu.add_cascade(label="Graphs", menu=self.workspace_menu)
        self.workspace_menu.add_command(label="Return to Trading Bot", command=self._open_trade_bot)

    def _open_trade_bot(self):

        graph_root.destroy()

        secret_key = MainMenu.user_secret_key
        public_key = MainMenu.user_public_key

        go_binance(secret_key, public_key)

    def _ask_before_close(self):

        """
        Triggered when the user click on the Close button of the interface.
        This lets you have control over what's happening just before closing the interface.
        :return:
        """

        result = askquestion("Confirmation", "Do you really want to exit TradeKing?")
        if result == "yes":
            self.destroy()  # Destroys the UI and terminates the program

#Hyperlink for Bitmex
def _open_browser_bitmax_keys():
    webbrowser.open_new("https://aivia.io/blog/en/how-to-get-an-api-key-on-bitmex-exchange/")

#Hyperlink for Binance
def _open_browser_binance_keys():
    webbrowser.open_new("https://dev.binance.vision/t/binance-testnet-environments/99/3")

#open graphs page function
def open_graph():
    global graph_root

    graph_root = Graph()
    graph_root.config(background=backgound_color)
    graph_root.geometry('1000x600')
    graph_root.mainloop()

#menu function
def open_main_menu():
    global main_menu_root

    main_menu_root = tk.Tk()
    MainMenu(main_menu_root)
    main_menu_root.mainloop()

#close application
def close_app():
    exit(0)

#connect to binance exchange
def go_binance(secret_key, public_key):
    # Create and configure the info_log object
    global trading_bot_root

    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)  # Overall minimum logging level

    stream_handler = logging.StreamHandler()  # Configure the logging messages displayed in the Terminal
    formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(new_log)s')
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)  # Minimum logging level for the StreamHandler

    file_handler = logging.FileHandler('info.log')  # Configure the logging messages written to a file
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Minimum logging level for the FileHandler

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    binance = BinanceClient(secret_key, public_key, testnet=True, futures=True)
    bitmex = BitmexClient(" ", " ", testnet=False)

    trading_bot_root = TradeKingRoot(binance, bitmex)
    trading_bot_root.mainloop()

#connect to bitmex exchange
def go_bitmex(secret_key, public_key):
    # Create and configure the info_log object
    global trading_bot_root

    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)  # Overall minimum logging level

    stream_handler = logging.StreamHandler()  # Configure the logging messages displayed in the Terminal
    formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(new_log)s')
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)  # Minimum logging level for the StreamHandler

    file_handler = logging.FileHandler('info.log')  # Configure the logging messages written to a file
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Minimum logging level for the FileHandler

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    binance = BinanceClient(" ", " ", testnet=False, futures=False)
    bitmex = BitmexClient(secret_key, public_key, testnet=True)

    trading_bot_root = TradeKingRoot(binance, bitmex)
    trading_bot_root.mainloop()

if __name__ == '__main__':
    """Top level code runner"""

    root = tk.Tk()
    MainMenu(root)
    root.mainloop()
