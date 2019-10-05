from typing import Any, Callable, Optional, Union

# from functools import partial, wraps

import tkinter as tk


class HoverInfo(tk.Menu):
    custom_init = partial(tk.Menu.__init__, relief="flat", bg="lightyellow", tearoff=0)

    def __init__(self, master: tk.Menu, text: str, delay: int) -> None:
        if not isinstance(text, str):
            fullname = text.__class__.__name__
            raise TypeError(
                "Trying to initialize a HoverInfo with a non str " f"type: {fullname}"
            )
        if not isinstance(delay, int):
            fullname = delay.__class__.__name__
            raise TypeError(
                "Trying to initialize a HoverInfo with non int " f"delay: {fullname}"
            )
        HoverInfo.custom_init(self, master)
        self.root = self._root()
        top_name = self.master.winfo_parent()
        self.top = self.root.nametowidget(top_name)
        print(f"{self.winfo_name()}'s master is {self.master.winfo_name()}")
        lines = [line.strip() for line in text.split(EOL)]
        for L in lines:
            self.add_command(label=L, state=tk.DISABLED)
        self.displaying = False
        self.delay = delay
        self.master.bind("<Enter>", self.onEnter)
        self.master.bind("<Motion>", self.onMotion)
        self.master.bind("<Leave>", self.onLeave)
        self.top.bind("<FocusOut>", self.onLeave)
        # When you call bind() a funcid is returned.
        # You can pass this funcid as the second parameter to unbind().

    def display(self, x, y):
        self.post(x, y)
        self.displaying = True

    def onEnter(self, event):
        x, y = event.x_root, event.y_root
        offset = int(tk.re.sub("[^0-9]", "", BORDER))
        x += offset
        y += offset
        if not self.displaying:
            self.queue = self.after(self.delay, self.display, x, y)
        # print(f"oi: {x}, {y}")

    def onMotion(self, event):
        # cx = self.winfo_pointerx() - self.winfo_rootx()
        # cy = self.winfo_pointery() - self.winfo_rooty()
        cx, cy = self.winfo_pointerxy()
        if self.displaying:
            # print(f"{cx}, {cy}")
            self.unpost()
            self.post(cx, cy)
            try:
                f = self.root.focus_get()
            except:
                print("No focus!")
            else:
                # _root returns not a name, but a Tk object!
                # root = self._root()
                # top_name = self.master.winfo_parent()
                # top = root.nametowidget(top_name)
                pass
                # r = self.root
                # t = self.top
                # print(f"focus is on {f}; root is {r}; top is {t} {type(t)}")
                # focus is on .; root is .; top is . <class 'tkinter.Tk'>
                # focus is on .!toplevel; root is .; top is .!toplevel <class
                # 'tkinter.Toplevel'>

    def onLeave(self, event):
        x, y = event.x_root, event.y_root
        if self.displaying:
            self.unpost()
        else:
            self.after_cancel(self.queue)
        self.displaying = False
        # print(f"tchau: {x}, {y}")
        # File "/home/daniel/Documents/Informática/git/morla/morla/gui.py", line 189, in onLeave
        # self.after_cancel(self.queue)
        # AttributeError: 'HoverInfo' object has no attribute 'queue'

    def __del__(self):
        try:
            self.top.unbind("<FocusOut>")
        except:
            print("Error:", "self.top.unbind('<FocusOut>')")
        else:
            print("Done:", "self.top.unbind('<FocusOut>')")
        return
        # if not isinstance(self.master, tk.Toplevel):
        master = self.winfo_toplevel()
        print(f"unbinding {master.winfo_name()}")
        master.unbind("<Enter>")
        master.unbind("<Motion>")
        master.unbind("<Leave>")


class FancyListbox(tk.Listbox):
    def __init__(self, parent, *args, **kwargs):
        # tk.Listbox.__init__(self, parent, *args, **kwargs)
        super(FancyListbox, self).__init__(parent, *args, **kwargs)
        #
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Delete", command=self.delete_selected)
        self.popup_menu.add_command(label="Select All", command=self.select_all)
        #
        self.bind("<Button-3>", self.popup)  # Button-2 on Aqua

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def delete_selected(self):
        for i in self.curselection()[::-1]:
            self.delete(i)

    def select_all(self):
        self.selection_set(0, tk.END)


if False:
    root = tk.Tk()
    flb = FancyListbox(root, selectmode="multiple")
    for n in range(10):
        flb.insert(tk.END, n)
    flb.grid()
    root.mainloop()
pass

r = tk.Tk()
t = ScrolledText(r)
t.grid()
r.mainloop()
