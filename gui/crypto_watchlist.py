import tkinter as tk
import typing
import tkmacosx as tkmac

from gui.styling import *
from gui.autocomplete_widget import CryptoAutocomplete
from gui.scrollable_frame import ScrollBar

from models import *

from database import WorkspaceData


class CryptoLive(tk.Frame):
    #pass the dictionary of the contracts for both exchanges
    def __init__(self, binance_contracts: typing.Dict[str, ExchangeContract], bitmex_contracts: typing.Dict[str, ExchangeContract],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = WorkspaceData()

        self.binance_symbols = list(binance_contracts.keys())
        self.bitmex_symbols = list(bitmex_contracts.keys())

        self._commands_frame = tk.Frame(self, bg=backgound_color)
        self._commands_frame.pack(side=tk.TOP)

        self._table_frame = tk.Frame(self, bg=backgound_color)
        self._table_frame.pack(side=tk.TOP)

        self._title_label = tk.Label(self._commands_frame, text="Crypto Prices:", bg=backgound_color, fg=foreground_color,
                                       font=BOLD_FONT2)
        self._title_label.grid(row=0, column = 1)

        self._title_label = tk.Label(self._commands_frame, text="Note: Only the connected\nExchange will display", bg=backgound_color,
                                     fg=foreground_color, font=main_font)
        self._title_label.grid(row=1, column=1)

        self._binance_label = tk.Label(self._commands_frame, text="Search Binance", bg=backgound_color, fg=foreground_color, font=BOLD_FONT)
        self._binance_label.grid(row=1, column=0)

        self._binance_crypto_entry = CryptoAutocomplete(self.binance_symbols, self._commands_frame, fg=foreground_color, justify=tk.CENTER,
                                                        insertbackground=foreground_color, bg=background_color_3, highlightthickness=False)
        self._binance_crypto_entry.bind("<Return>", self._add_binance_symbol)
        self._binance_crypto_entry.grid(row=2, column=0,pady = 8)

        self._bitmex_label = tk.Label(self._commands_frame, text="Search Bitmex", bg=backgound_color, fg=foreground_color, font=BOLD_FONT)
        self._bitmex_label.grid(row=1, column=2)

        self._bitmex_crypto_entry = CryptoAutocomplete(self.bitmex_symbols, self._commands_frame, fg=foreground_color, justify=tk.CENTER,
                                                       insertbackground=foreground_color, bg=background_color_3, highlightthickness=False)
        self._bitmex_crypto_entry.bind("<Return>", self._add_bitmex_symbol)
        self._bitmex_crypto_entry.grid(row=2, column=2, pady = 8)

        self.body_widgets = dict()

        self._headers = ["exchange", "symbol",  "bid", "ask", "remove"]

        self._headers_frame = tk.Frame(self._table_frame, bg=backgound_color)

        self._col_width = 13

        # Creates the headers dynamically

        for idx, h in enumerate(self._headers):
            header = tk.Label(self._headers_frame, text=h.capitalize() if h != "remove" else "", bg=backgound_color,
                              fg=foreground_color, font=main_font, width=self._col_width)
            header.grid(row=0, column=idx)

        header = tk.Label(self._headers_frame, text="", bg=backgound_color,
                          fg=foreground_color, font=main_font, width=2)
        header.grid(row=0, column=len(self._headers))

        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        # Creates the table body

        self._body_frame = ScrollBar(self._table_frame, bg=backgound_color, height=250)
        self._body_frame.pack(side=tk.TOP, fill=tk.X, anchor="nw")

        # Add keys to the trades_col dictionary, the keys represents columns or data related to a column
        # You could also have another logic: instead of trades_col[column][row] have trades_col[row][column]
        for h in self._headers:
            self.body_widgets[h] = dict()
            if h in ["bid", "ask"]:
                self.body_widgets[h + "_var"] = dict()

        self._body_index = 0

        # Loads the CryptoLive symbols saved to the database during a previous session
        saved_symbols = self.db.get("watchlist")

        for s in saved_symbols:
            self._add_symbol(s['symbol'], s['exchange'])


    def _add_bitmex_symbol(self, event):
        symbol = event.widget.get()

        if symbol in self.bitmex_symbols:
            self._add_symbol(symbol, "Bitmex")
            event.widget.delete(0, tk.END)

    def _add_binance_symbol(self, event):
        symbol = event.widget.get()

        if symbol in self.binance_symbols:
            self._add_symbol(symbol, "Binance")
            event.widget.delete(0, tk.END)

    def _remove_symbol(self, b_index: int):

        for h in self._headers:
            #Call the grid forget and delte the specific ID from the grid dictonary
            self.body_widgets[h][b_index].grid_forget()
            del self.body_widgets[h][b_index]

    def _add_symbol(self, symbol: str, exchange: str):

        body_index = self._body_index

        self.body_widgets['exchange'][body_index] = tk.Label(self._body_frame.sub_frame, text=exchange, bg=backgound_color,
                                                          fg=foreground_color_binance, font=main_font, width=self._col_width)
        self.body_widgets['exchange'][body_index].grid(row=body_index, column=0)


        self.body_widgets['symbol'][body_index] = tk.Label(self._body_frame.sub_frame, text=symbol, bg=backgound_color,
                                                           fg=foreground_color_4, font=main_font, width=self._col_width)
        self.body_widgets['symbol'][body_index].grid(row=body_index, column=1)



        self.body_widgets['bid_var'][body_index] = tk.StringVar()
        self.body_widgets['bid'][body_index] = tk.Label(self._body_frame.sub_frame,
                                                        textvariable=self.body_widgets['bid_var'][body_index],
                                                        bg=backgound_color, fg=ufo_green, font=main_font,
                                                        width=self._col_width)
        self.body_widgets['bid'][body_index].grid(row=body_index, column=2)

        self.body_widgets['ask_var'][body_index] = tk.StringVar()
        self.body_widgets['ask'][body_index] = tk.Label(self._body_frame.sub_frame,
                                                        textvariable=self.body_widgets['ask_var'][body_index],
                                                        bg=backgound_color, fg=ufo_green, font=main_font,
                                                        width=self._col_width)
        self.body_widgets['ask'][body_index].grid(row=body_index, column=3)

        self.body_widgets['remove'][body_index] = tkmac.Button(self._body_frame.sub_frame, text="X", borderless = True,
                                                            bg="#ff4757", fg=foreground_color, font=main_font,
                                                            command=lambda: self._remove_symbol(body_index), width=30)
        self.body_widgets['remove'][body_index].grid(row=body_index, column=4)

        self._body_index += 1
