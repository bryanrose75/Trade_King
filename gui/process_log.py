import tkinter as tk
from datetime import datetime
from gui.styling import *

class ProcessLog(tk.Frame): #Log the orders into the GUI terminal to remove the need of checking the python terminal
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.process_log_text = tk.Text(self, height=15, width=70, state=tk.DISABLED, bg=backgound_color, fg=foreground_color_4,
                                        font=main_font, highlightthickness=True, bd=0, padx=5, pady=5)
        self.process_log_text.pack(side=tk.TOP)

    def add_log(self, new_log: str):
        #Create a new log new_log

        self.process_log_text.configure(state=tk.NORMAL)
        self.process_log_text.insert("1.0", datetime.now().strftime("%a %H:%M:%S :: ") + new_log + "\n")

        # Freeze window
        self.process_log_text.configure(state=tk.DISABLED)

