import tkinter as tk


from models import *

from gui.scrollable_frame import ScrollBar
from gui.styling import *



class UserTrades(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_trades_frame = tk.Frame(self, bg=backgound_color)
        self.user_trades_frame.pack(side=tk.TOP)
        self.title_frame = tk.Frame(self.user_trades_frame, bg=backgound_color)

        self.user_trades_titles = ["time", "exchange", "symbol", "strategy", "side", "size", "profitloss", "status"]

        self._col_width = 12  # Fixed headers width to match the table body width

        self.trades_col = dict()



        for idx, h in enumerate(self.user_trades_titles):
            header = tk.Label(self.title_frame, text=h.capitalize(), bg=backgound_color,
                              fg=foreground_color, font=main_font, width=self._col_width)
            header.grid(row=0, column=idx)

        header = tk.Label(self.title_frame, text="", bg=backgound_color,
                          fg=foreground_color, font=main_font, width=2)
        header.grid(row=0, column=len(self.user_trades_titles))

        self.title_frame.pack(side=tk.TOP, anchor="nw")

        for h in self.user_trades_titles:
            self.trades_col[h] = dict()
            if h in ["status", "profitloss", "size"]:
                self.trades_col[h + "_var"] = dict()

        self._body_index = 0

        self._body_frame = ScrollBar(self, bg=backgound_color, height=250)
        self._body_frame.pack(side=tk.TOP, anchor="nw", fill=tk.X)

    def add_trade(self, trade: Trade):


        body_i = self._body_index

        trade_i = trade.time  # This is used as a trade identifier

        dt_str = datetime.datetime.fromtimestamp(trade.time / 1000).strftime("%b %d %H:%M")

        # Size
        self.trades_col['size_var'][
            trade_i] = tk.StringVar()  # Variable because the order is not always filled immediately
        self.trades_col['size'][trade_i] = tk.Label(self._body_frame.sub_frame,
                                                    textvariable=self.trades_col['size_var'][trade_i],
                                                    bg=backgound_color, font=main_font, fg=foreground_color_4,
                                                    width=self._col_width)
        self.trades_col['size'][trade_i].grid(row=body_i, column=5)


        # Side
        self.trades_col['side'][trade_i] = tk.Label(self._body_frame.sub_frame, text=trade.side.capitalize(),
                                                    bg=backgound_color, font=main_font, fg=foreground_color_4, width=self._col_width)
        self.trades_col['side'][trade_i].grid(row=body_i, column=4)

        # PNL
        self.trades_col['pnl_var'][trade_i] = tk.StringVar()
        self.trades_col['profitloss'][trade_i] = tk.Label(self._body_frame.sub_frame,
                                                          textvariable=self.trades_col['pnl_var'][trade_i], bg=backgound_color, font=main_font,
                                                          fg=ufo_green, width=self._col_width)
        self.trades_col['profitloss'][trade_i].grid(row=body_i, column=6)

        self._body_index += 1

        # Status
        self.trades_col['status_var'][trade_i] = tk.StringVar()
        self.trades_col['status'][trade_i] = tk.Label(self._body_frame.sub_frame,
                                                      textvariable=self.trades_col['status_var'][trade_i],
                                                      bg=backgound_color, font=main_font, fg="#ff4757",
                                                      width=self._col_width)
        self.trades_col['status'][trade_i].grid(row=body_i, column=7)

        # Strategy
        self.trades_col['strategy'][trade_i] = tk.Label(self._body_frame.sub_frame, font=main_font, text=trade.strategy,
                                                        bg=backgound_color,
                                                        fg=foreground_color_4,
                                                        width=self._col_width)
        self.trades_col['strategy'][trade_i].grid(row=body_i, column=3)

        #Time
        self.trades_col['time'][trade_i] = tk.Label(self._body_frame.sub_frame, text=dt_str, font=main_font, bg=backgound_color,
                                                    fg="#ced6e0", width=self._col_width)
        self.trades_col['time'][trade_i].grid(row=body_i, column=0)

        # Exchange

        self.trades_col['exchange'][trade_i] = tk.Label(self._body_frame.sub_frame,
                                                        text=trade.contract.exchange.capitalize(),
                                                        bg=backgound_color, fg=foreground_color_binance,
                                                        width=self._col_width, font=main_font)
        self.trades_col['exchange'][trade_i].grid(row=body_i, column=1)

        # Symbol

        self.trades_col['symbol'][trade_i] = tk.Label(self._body_frame.sub_frame, text=trade.contract.symbol,
                                                      bg=backgound_color, font=main_font, fg=foreground_color_4,
                                                      width=self._col_width)
        self.trades_col['symbol'][trade_i].grid(row=body_i, column=2)














