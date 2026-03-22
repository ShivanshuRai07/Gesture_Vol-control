import tkinter as tk
from tkinter import Menu

class FloatingMenu:
    def __init__(self, on_toggle_control, on_toggle_live_view, on_quit):
        self.root = tk.Tk()
        self.root.title("Gesture Control Menu")
        
        # Window properties - using standard window for maximum compatibility
        self.root.attributes("-topmost", True)
        self.root.geometry("80x80+300+300")  # Slightly larger for standard window
        self.root.config(bg='#0078d7')
        
        self._x = 0
        self._y = 0
        
        self.canvas = tk.Canvas(self.root, width=60, height=60, bg='#0078d7', highlightthickness=0)
        self.canvas.pack()
        
        # Draw the blue circle
        self.circle = self.canvas.create_oval(2, 2, 58, 58, fill='#0078d7', outline='white', width=2)
        
        # Ensure it's shown
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        # Callbacks
        self.on_toggle_control = on_toggle_control
        self.on_toggle_live_view = on_toggle_live_view
        self.on_quit = on_quit
        
        # Dragging logic
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        self.canvas.bind("<Button-3>", self.show_menu) # Right click
        self.canvas.bind("<Button-1>", self.show_menu) # Left click also shows menu for ease

        # Context Menu
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="Toggle Gesture Control", command=self.on_toggle_control)
        self.menu.add_command(label="Show/Hide Live View", command=self.on_toggle_live_view)
        self.menu.add_separator()
        self.menu.add_command(label="Exit App", command=self.on_quit)

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + event.x - self._x
        y = self.root.winfo_y() + event.y - self._y
        self.root.geometry(f"+{x}+{y}")

    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def run(self):
        self.root.mainloop()

    def update(self):
        self.root.update()
