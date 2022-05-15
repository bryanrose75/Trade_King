import tkinter as tk



class ScrollBar(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #This widgets draws a Frame inside a Canvas widget so that the canvas scrolling will actually scroll the Frame inside it.
        self.canvas = tk.Canvas(self, highlightthickness=0, **kwargs)
        self.vsb = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.sub_frame = tk.Frame(self.canvas, **kwargs)

        self.sub_frame.bind("<Configure>", self._on_frame_configure)
        self.sub_frame.bind("<Leave>", self._deactivate_mousewheel)
        self.sub_frame.bind("<Enter>", self._activate_mousewheel)

        self.canvas.configure(yscrollcommand=self.vsb.set)  # Link the scrollbar and canvas together
        self.canvas.create_window((0, 0), window=self.sub_frame, anchor="nw")  # Places the sub_frame in the canvas

        self.canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)  # Makes sure the scrollbar expands to the full Frame height

    def _on_mousewheel(self, event: tk.Event):


        #Scroll the canvas content when the MouseWheel is triggered.


        self.canvas.yview_scroll(int(-1 * (event.delta / 60)), "units")  # Decrease 60 to increase the sensitivity



    def _on_frame_configure(self, event: tk.Event):


        #Makes the whole canvas content (defined by the .bbox("all") coordinates) scrollable.


        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _deactivate_mousewheel(self, event: tk.Event):


        #Deactivate the _on_mousewheel() callback when the mouse leaves the canvas sub_frame


        self.canvas.unbind_all("<MouseWheel>")

    def _activate_mousewheel(self, event: tk.Event):


        #Activate the _on_mousewheel() callback when the mouse enters the canvas sub_frame


        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)















