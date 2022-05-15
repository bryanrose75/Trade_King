import tkinter as tk
import typing


class CryptoAutocomplete(tk.Entry):
    def __init__(self, symbols: typing.List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._symbols = symbols

        self._ac_listbox: tk.Listbox
        self.listbox_open = False  # Used to know whether the Listbox is already open or not

        self.bind("<Right>", self.right_key) # bind to the keyboard
        self.bind("<Up>", self.down_up_key)
        self.bind("<Down>", self.down_up_key)


        self._var = tk.StringVar()
        self.configure(textvariable=self._var)  # Links the tk.Entry content to a StringVar()
        self._var.trace("w", self._changed)  # When the self._var value changes



    def down_up_key(self, event: tk.Event):


        #Move the Listbox cursor up or down depending on the keyboard key that was pressed.


        if self.listbox_open:
            if self._ac_listbox.curselection() == ():  # No Listbox item selected yet
                crypto_index = -1
            else:
                crypto_index = self._ac_listbox.curselection()[0]

            lb_size = self._ac_listbox.size()

            if crypto_index > 0 and event.keysym == "Up":
                self._ac_listbox.select_clear(first=crypto_index)
                crypto_index = str(crypto_index - 1)
                self._ac_listbox.selection_set(first=crypto_index)
                self._ac_listbox.activate(crypto_index)
            elif crypto_index < lb_size - 1 and event.keysym == "Down":
                self._ac_listbox.select_clear(first=crypto_index)
                crypto_index = str(crypto_index + 1)
                self._ac_listbox.selection_set(first=crypto_index)
                self._ac_listbox.activate(crypto_index)

    def right_key(self, event: tk.Event):


        #Triggered with when the keyboard Right arrow is pressed, set the current Listbox item as a value of the


        if self.listbox_open:
            self._var.set(self._ac_listbox.get(tk.ACTIVE))
            self._ac_listbox.destroy()
            self.listbox_open = False
            self.icursor(tk.END)

    def _changed(self, index: str, var_name: str,  mode: str):

        #Open a Listbox when the tk.Entry content changes and get a list of symbols matching this content

        self._var.set(self._var.get().upper())  # Set the content of the tk.Entry widget to uppercase as you type

        if self._var.get() == "":  # Closes the Listbox when the tk.Entry is empty
            if self.listbox_open:
                self._ac_listbox.destroy()
                self.listbox_open = False
        else:
            if not self.listbox_open:
                self._ac_listbox = tk.Listbox(height=8)  # Limits the number of items displayed in the Listbox
                self._ac_listbox.place(x=self.winfo_x() + self.winfo_width() - 170, y=self.winfo_y() + self.winfo_height() + 25)

                self.listbox_open = True

            # Finds symbols that start with the characters that you typed in the tk.Entry widget
            symbols_matched = [symbol for symbol in self._symbols if symbol.startswith(self._var.get())]

            if len(symbols_matched) > 0:

                try:
                    self._ac_listbox.delete(0, tk.END)
                except tk.TclError:
                    pass

                for symbol in symbols_matched[:8]:  # Takes only the first 8 elements of the list to match the Listbox
                    self._ac_listbox.insert(tk.END, symbol)

            else:  # If no match, closes the Listbox if it was open
                if self.listbox_open:
                    self._ac_listbox.destroy()
                    self.listbox_open = False


