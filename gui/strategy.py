import tkinter as tk
import typing
import tkmacosx as tkmac
import webbrowser

import json

from exchanges.binance import BinanceClient
from exchanges.bitmex import BitmexClient

from strategies import TechnicalStrategy, BreakoutStrategy
from utils import *

from database import WorkspaceData
from gui.styling import *
from gui.scrollable_frame import ScrollBar

if typing.TYPE_CHECKING:
    from main import TradeKingRoot


class TradingStrategy(tk.Frame):
    def __init__(self, root: "TradeKingRoot", binance: BinanceClient, bitmex: BitmexClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = WorkspaceData()
        self.root = root

        self._valid_float = self.register(validate_float_format)# Check if there is a valid entry
        self._valid_integer = self.register(validate_integer_format)# Check if there is a valid entry

        self._exchanges = {"Binance": binance, "Bitmex": bitmex}

        self._all_contracts = []
        self._all_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h"]

        for exchange, client in self._exchanges.items():
            for symbol, contract in client.contracts.items():
                # If you want less symbols in the list, filter here (there are a lot of pairs on Binance Spot)
                self._all_contracts.append(symbol + "_" + exchange.capitalize())

        self._command_F = tk.Frame(self, bg=backgound_color)  # Set the command frames
        self._command_F.pack(side=tk.TOP)


        self._table_F = tk.Frame(self, bg=backgound_color) # Set the table frames
        self._table_F.pack(side=tk.TOP)



        # Button Creation
        self._add_b_strategy = tkmac.Button(self._command_F, text="Add strategy", font=main_font,
                                            command=self.add_strategy_row, bg=background_color_2, fg=foreground_color,
                                            borderless=True)
        self._add_b_strategy.pack(side=tk.TOP)
        self._add_b_definitions = tkmac.Button(self._command_F, text="Definitions", font=main_font,
                                               command=self.open_browser, bg=background_color_3, fg=foreground_color,
                                               borderless=True)
        self._add_b_definitions.pack(side=tk.TOP)

        self._headers_frame = tk.Frame(self._table_F, bg=backgound_color)


        self._extra_input = dict()
        self.additional_parameters = dict()
        self.body_widgets = dict()


        # Defines the widgets displayed on each row and some characteristics of these widgets like their width
        # This lets the program create the widgets dynamically and it takes less space in the code
        # The width may need to be adjusted depending on your screen size and resolution
        self._base_parameters = [
            {"code_name": "strategy_type", "widget": tk.OptionMenu, "data_type": str,
             "values": ["Technical", "Breakout"], "width": 12, "headers": "Strategy"},
            {"code_name": "contract", "widget": tk.OptionMenu, "data_type": str, "values": self._all_contracts,
             "width": 18, "headers": "Contract"},
            {"code_name": "timeframe", "widget": tk.OptionMenu, "data_type": str, "values": self._all_timeframes,
             "width": 10, "headers": "Timeframe"},
            {"code_name": "balance_pct", "widget": tk.Entry, "data_type": float, "width": 15, "headers": "Balance %"},
            {"code_name": "stop_loss", "widget": tk.Entry, "data_type": float, "width": 15, "headers": "Stop Loss %"},
            {"code_name": "take_profit", "widget": tk.Entry, "data_type": float, "width": 15,
             "headers": "Take Profit %"},
            {"code_name": "parameters", "widget": tk.Button, "data_type": float, "text": "Params",
             "bg": background_color_2, "command": self.show_popup, "headers": "", "width": 50},
            {"code_name": "activation", "widget": tk.Button, "data_type": float, "text": "OFF",
             "bg": "#ff4757", "command": self.switch_strategy, "headers": "", "width": 30},
            {"code_name": "delete", "widget": tk.Button, "data_type": float, "text": "X",
             "bg": "#ff4757", "command": self.delete_row, "headers": "", "width": 30},

        ]

        self.extra_params = {
            "Technical": [
                {"code_name": "rsi_length", "name": "RSI Periods", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_slow", "name": "MACD Slow Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_fast", "name": "MACD Fast Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_signal", "name": "MACD Signal Length", "widget": tk.Entry, "data_type": int},
            ],
            "Breakout": [
                {"code_name": "min_volume", "name": "Min Volume", "widget": tk.Entry, "data_type": float},
            ]
        }

        for idx, h in enumerate(self._base_parameters):
            headers = tk.Label(self._headers_frame, text=h['headers'], bg=backgound_color, fg=foreground_color,
                              font=BOLD_FONT, width=h['width'], bd=1, relief=tk.FLAT)
            headers.grid(row=0, column=idx, padx=2)

        headers = tk.Label(self._headers_frame, text="", bg=backgound_color, fg=foreground_color, font=main_font,
                          width=8, bd=1, relief=tk.FLAT)
        headers.grid(row=0, column=len(self._base_parameters), padx=2)

        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        self._body_frame = ScrollBar(self._table_F, bg=backgound_color, height=250)
        self._body_frame.pack(side=tk.TOP, fill=tk.X, anchor="nw")

        for h in self._base_parameters:
            self.body_widgets[h['code_name']] = dict()
            if h['code_name'] in ["strategy_type", "contract", "timeframe"]:
                self.body_widgets[h['code_name'] + "_var"] = dict()

        self._body_index = 0

        self.load_workspace()

    def add_strategy_row(self):

        body_i = self._body_index

        for col, base_param in enumerate(self._base_parameters):
            code_name = base_param['code_name']
            if base_param['widget'] == tk.OptionMenu:
                self.body_widgets[code_name + "_var"][body_i] = tk.StringVar()
                self.body_widgets[code_name + "_var"][body_i].set(base_param['values'][0])
                self.body_widgets[code_name][body_i] = tk.OptionMenu(self._body_frame.sub_frame,
                                                                      self.body_widgets[code_name + "_var"][body_i],
                                                                      *base_param['values'])
                self.body_widgets[code_name][body_i].config(width=base_param['width'], highlightthickness=False,
                                                             bd=-1, font=main_font, indicatoron=0, bg=backgound_color)

            elif base_param['widget'] == tk.Button:
                self.body_widgets[code_name][body_i] = tkmac.Button(self._body_frame.sub_frame,
                                                                     text=base_param['text'],
                                                                     bg=base_param['bg'], fg=foreground_color,
                                                                     borderless=True, font=main_font,
                                                                     width=base_param['width'],
                                                                     command=lambda frozen_command=base_param[
                                                                         'command']: frozen_command(body_i))

            elif base_param['widget'] == tk.Entry:
                self.body_widgets[code_name][body_i] = tk.Entry(self._body_frame.sub_frame, justify=tk.CENTER,
                                                                 bg=background_color_3, fg=foreground_color,
                                                                 highlightthickness=False,
                                                                 font=main_font, bd=0, width=base_param['width'])
                # %P shows that what is passed is the new text alternatively %s is before the text

                if base_param['data_type'] == float:
                    self.body_widgets[code_name][body_i].config(validate='key',
                                                             validatecommand=(self._valid_float, "%P"))
                elif base_param['data_type'] == int:
                    self.body_widgets[code_name][body_i].config(validate='key',
                                                                 validatecommand=(self._valid_integer, "%P"))


            else:
                continue

            self.body_widgets[code_name][body_i].grid(row=body_i, column=col, padx=2)

        self.additional_parameters[body_i] = dict()

        for strat, params in self.extra_params.items():
            for param in params:
                self.additional_parameters[body_i][param['code_name']] = None

        self._body_index += 1

    def show_popup(self, b_index: int):

        # Display a popup window with additional parameters that are specific to the selected strategy
        # This is to avoid overloading the strategy component with too many tk.Entry boxes.

        y = self.body_widgets["parameters"][b_index].winfo_rooty()
        x = self.body_widgets["parameters"][b_index].winfo_rootx()

        self.parameters_popup_window = tk.Toplevel(self)
        self.parameters_popup_window.wm_title("Parameters")

        self.parameters_popup_window.config(bg=backgound_color)
        self.parameters_popup_window.attributes("-topmost", "true")
        self.parameters_popup_window.grab_set()

        self.parameters_popup_window.geometry(f"+{x - 80}+{y + 30}")

        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()

        row_nb = 0

        for param in self.extra_params[strategy_selected]:
            code_name = param['code_name']

            temp_label = tk.Label(self.parameters_popup_window, bg=backgound_color, fg=foreground_color,
                                  text=param['name'],
                                  font=BOLD_FONT)
            temp_label.grid(row=row_nb, column=0)

            if param['widget'] == tk.Entry:
                self._extra_input[code_name] = tk.Entry(self.parameters_popup_window, bg=background_color_3,
                                                        justify=tk.CENTER,
                                                        fg=foreground_color,
                                                        insertbackground=foreground_color, highlightthickness=False)
                """Validate how the call back function will be triggered, TradeKing reacts to keyboard entries but 
                    alternatives are - 
                    :Focus
                    :Focusin
                    :Focusout
                    :all             
                """
                # Sets the data validation function based on the data_type chosen
                if param['data_type'] == int:
                    self._extra_input[code_name].config(validate='key', validatecommand=(self._valid_integer, "%P"))
                # %P shows that what is passed is the new text alternatively %s is before the text
                elif param['data_type'] == float:
                    self._extra_input[code_name].config(validate='key', validatecommand=(self._valid_float, "%P"))

                if self.additional_parameters[b_index][code_name] is not None:
                    self._extra_input[code_name].insert(tk.END, str(self.additional_parameters[b_index][code_name]))
            else:
                continue

            self._extra_input[code_name].grid(row=row_nb, column=1)

            row_nb += 1

        # Validation Button

        validation_button = tkmac.Button(self.parameters_popup_window, text="Validate", bg=background_color_2,
                                         fg=foreground_color,
                                         command=lambda: self.validate_parameters(b_index), borderless=True)
        validation_button.grid(row=row_nb, column=0, columnspan=2)


    def delete_row(self, b_index: int):

        # Triggered when the user clicks the X button.
        # The row below the one deleted will automatically adjust and take its place, independently of its b_index.

        for element in self._base_parameters:
            self.body_widgets[element['code_name']][b_index].grid_forget()

            del self.body_widgets[element['code_name']][b_index]

    def open_browser(self):
        webbrowser.open_new("https://www.firstrade.com/content/en-us/education/glossary?&letter=s")

    def switch_strategy(self, b_index: int):

        # Activates when pressing the ON/OFF button.
        # Collects initial historical data (hence why there is a small delay on the gui after you click).

        for param in ["balance_pct", "take_profit", "stop_loss"]:
            if self.body_widgets[param][b_index].get() == "":
                self.root._process_log.add_log(f"Missing {param} parameter")
                return

        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self.extra_params[strat_selected]:
            if self.additional_parameters[b_index][param['code_name']] is None:
                self.root._process_log.add_log(f"Missing {param['code_name']} parameter")
                return

        symbol = self.body_widgets['contract_var'][b_index].get().split("_")[0]
        timeframe = self.body_widgets['timeframe_var'][b_index].get()
        exchange = self.body_widgets['contract_var'][b_index].get().split("_")[1]

        contract = self._exchanges[exchange].contracts[symbol]

        balance_pct = float(self.body_widgets['balance_pct'][b_index].get())
        take_profit = float(self.body_widgets['take_profit'][b_index].get())
        stop_loss = float(self.body_widgets['stop_loss'][b_index].get())

        if self.body_widgets['activation'][b_index].cget("text") == "OFF":

            if strat_selected == "Technical":
                # Getting historical data
                new_strategy = TechnicalStrategy(self._exchanges[exchange], contract, exchange, timeframe, balance_pct,
                                                 take_profit, stop_loss, self.additional_parameters[b_index])
            elif strat_selected == "Breakout":
                new_strategy = BreakoutStrategy(self._exchanges[exchange], contract, exchange, timeframe, balance_pct,
                                                take_profit, stop_loss, self.additional_parameters[b_index])
            else:  # otherwise continue
                return

            # Collects historical data is just one API call
            # making a query to a database containing billions of rows would freeze the gui.
            new_strategy.candles = self._exchanges[exchange]._historical_data(contract, timeframe)

            # There was an error during the request
            # Inform the user about the error
            if len(new_strategy.candles) == 0:
                self.root._process_log.add_log(f"Error: No historical data retrieved for {contract.symbol}")
                return
            new_strategy._check_signal()

            if exchange == "Binance":
                self._exchanges[exchange].subscribe_channel([contract], "aggTrade")
                self._exchanges[exchange].subscribe_channel([contract], "bookTicker")

            self._exchanges[exchange].strategies[b_index] = new_strategy

            for param in self._base_parameters:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.DISABLED)  # Locks the widgets of this row

            self.body_widgets['activation'][b_index].config(bg="#2ed573", text="ON")
            self.root._process_log.add_log(f"{strat_selected} strategy on {symbol} / {timeframe} started")

        else:
            #Select the client
            #select the variable
            #select the key
            del self._exchanges[exchange].strategies[b_index]

            for param in self._base_parameters:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.NORMAL)

            self.body_widgets['activation'][b_index].config(bg="#ff4757", text="OFF")
            self.root._process_log.add_log(f"{strat_selected} strategy on {symbol} / {timeframe} stopped")


    def validate_parameters(self, b_index: int):

        # Record the parameters set in the popup window and then close it.

        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self.extra_params[strategy_selected]:
            code_name = param['code_name']

            if self._extra_input[code_name].get() == "":
                self.additional_parameters[b_index][code_name] = None
            else:
                self.additional_parameters[b_index][code_name] = param['data_type'](self._extra_input[code_name].get())

        self.parameters_popup_window.destroy()


    def load_workspace(self):

        # Add the rows and fill them with data saved in the database
        data = self.db.get("strategies")

        for row in data:
            self.add_strategy_row()

            b_index = self._body_index - 1  # -1 to select the row that was just added

            for base_param in self._base_parameters:
                code_name = base_param['code_name']

                if base_param['widget'] == tk.OptionMenu and row[code_name] is not None:
                    self.body_widgets[code_name + "_var"][b_index].set(row[code_name])
                elif base_param['widget'] == tk.Entry and row[code_name] is not None:
                    self.body_widgets[code_name][b_index].insert(tk.END, row[code_name])

            extra_params = json.loads(row['extra_params'])

            for param, value in extra_params.items():
                if value is not None:
                    self.additional_parameters[b_index][param] = value
