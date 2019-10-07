# -*- coding: utf-8 -*-

from typing import Callable, Iterable, List, Union  # , TypeVar

# sys is already loaded by tkinter; use tk.sys instead
# import base64
from functools import partial, wraps
from contextlib import redirect_stdout, redirect_stderr
import io

# import webbrowser as browser

from tkinter.scrolledtext import ScrolledText as tkScrolledText
from tkinter.constants import RAISED, SUNKEN, FLAT, RIDGE, GROOVE, SOLID
from tkinter import ttk
import tkinter as tk

from morla.utils import *
from morla.configuration import Configuration


# GUI constants
BORDER = "3p"

# tkinter stuff
STATE = "state"
NORMAL = "normal"
ENABLED = "enabled"
DISABLED = "disabled"
RIGHT_MOUSE = "<Button-3>"


class ScrolledText(tkScrolledText):
    """Like tkinter.scrolledtext.ScrolledText, but with a tk.Menu that pops at right
    mouse clicks and lets the user select the entire text and/or clear the part selected
    (even if the text is disabled!)
    tk.ScrolledText:
    https://github.com/python/cpython/blob/3.6/Lib/tkinter/scrolledtext.py
    """

    def __init__(self, master=None, **kw):
        super(ScrolledText, self).__init__(master=master, **kw)
        root = self.nametowidget(".!morlaframe")
        # pop-up menu
        self.tooltip = tk.Menu(self, tearoff=0)
        # "select all" option
        sel_all = partial(select_all, self)
        sel_all_word = root.get_string("select_all")
        self.tooltip.add_command(label=sel_all_word, command=sel_all)
        # "clear selected" option
        clear_sel = partial(clear_selected_text, self)
        clear_word = root.get_string("clear")
        self.tooltip.add_command(label=clear_word, command=clear_sel)
        self.bind(RIGHT_MOUSE, self.on_right_click)

    def on_right_click(self, event):
        print(f"> {event}")
        try:
            self.tooltip.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.tooltip.grab_release()

    def highlight_pattern(self, pattern, tag, start="1.0", end=tk.END, regexp=False):
        """Apply the given tag to all text that matches the given pattern. If 'regexp'
        is set to True, pattern will be treated as a regular expression according to
        Tcl's regular expression syntax.
        """
        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)
        count = tk.IntVar()
        while True:
            index = self.search(
                pattern, "matchEnd", "searchLimit", count=count, regexp=regexp
            )
            if index == "":
                break
            if count.get() == 0:
                break  # degenerate pattern which matches zero-length strings
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")


class CustomButton(tk.Button):
    def __init__(self, master, *args, **kwargs) -> None:
        # tk.Button's __init__: (self, master=None, cnf={}, **kw)
        super(CustomButton, self).__init__(master, *args, **kwargs)
        self.config(cursor="mouse", pady=BORDER)


class CustomToplevel(tk.Toplevel):
    """A Toplevel widget with __enter__ and __exit__ methods, which allows for it to be
    used as a context manager.
    Code for tk.Toplevel:
    https://github.com/python/cpython/blob/f1f9c0c532089824791cfc18e6d6f29e1cd62596/Lib/tkinter/__init__.py#L2320
    """

    def __init__(
        self,
        master,
        # *args,
        title: str = None,
        exclusive: bool = True,
        plain: bool = False,
        **kwargs,
    ) -> None:
        # tk.Toplevel's __init__: (self, master=None, cnf={}, **kw)
        super(CustomToplevel, self).__init__(master, relief=FLAT, borderwidth=BORDER)
        self.resizable(False, False)
        if title:
            self.title(title)
        if exclusive:
            self.grab_set()
        if plain:
            self.overrideredirect(True)
        # self.focus_set()
        self.focus_force()
        self.lift()

    def __enter__(self) -> "CustomToplevel":
        name = str(self)
        print(f"> calling {name}.__enter__")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object. The parameters
        describe the exception that caused the context to be exited. If the
        context was exited without an exception, all three arguments will be
        None. If an exception is supplied, and the method wishes to suppress
        the exception (i.e., prevent it from being propagated), it should
        return a true value. Otherwise, the exception will be processed
        normally upon exit from this method.
        Note that __exit__() methods should not reraise the passed-in
        exception; this is the caller’s responsibility.
        """
        name = str(self)
        print(f"> calling {name}.__exit__")
        self.destroy()


def zoom(widget: tk.Tk, value: Optional[bool] = None) -> bool:
    if value in (True, False):
        widget.wm_attributes("-zoomed", value)
    elif value is not None:
        raise ValueError("value must be bool or None")
    return widget.wm_attributes("-zoomed")


def center(win: Union[tk.Tk, tk.Toplevel]) -> None:
    """Centers a tkinter window.
    https://stackoverflow.com/a/10018670
    :param win: the tk.Tk or tk.Toplevel window to center
    """
    # changing the cursor
    top = win.winfo_toplevel()
    top.config(cursor="watch")
    # making the window invisible
    win.wm_attributes("-alpha", 0.0)  # .attributes
    # drawing everything
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry(f"{width}x{height}+{x}+{y}")
    # making the window visible
    win.wm_attributes("-alpha", 1.0)
    # restoring the cursor
    top.config(cursor="")
    # done!
    win.deiconify()
    win.update_idletasks()


def clear_widgets(widget: tk.Widget) -> None:
    for child in widget.winfo_children():
        child.destroy()


def get_nb_buttons(nb: ttk.Notebook) -> List[tk.Button]:
    """Fetchs a list with all the buttons in every tab of a ttk Notebook.
    """
    L = []
    for tab in nb.winfo_children():
        # print("> tab:", tab)
        for obj in tab.winfo_children():
            # print("> obj:", obj, type(obj))
            if isinstance(obj, (tk.Checkbutton, tk.Radiobutton)):
                L.append(obj)
    return L


def _foobar(buttons: List[tk.Button]) -> None:
    for btn in buttons:
        btn_name = str(btn).split(".")[-2:]
        btn_name = "".join(btn_name)
        print(btn_name)
        # print(list(btn.config().keys()))
        # continue
        for key in ("variable", "value", "onvalue", "offvalue", "textvariable"):
            try:
                v = btn.cget(key)
            except tk.TclError:
                pass
            else:
                print(">", v, type(v))
    return


def open_toplevel(
    master: tk.Tk, title: str = None, exclusive: bool = True
) -> tk.Toplevel:
    window = tk.Toplevel(master, relief=FLAT, borderwidth=BORDER)
    #
    window.resizable(False, False)
    if title:
        window.title(title)
    if exclusive:
        window.grab_set()
    # window.focus_set()
    window.focus_force()
    window.lift()
    return window


def toggleText(t: tk.Text) -> str:
    if t[STATE] == NORMAL:
        t.config(state=DISABLED)
    elif t[STATE] == DISABLED:
        t.config(state=NORMAL)
    else:
        msg = f"t['state'] should be 'normal' or 'disabled', not {t[STATE]}."
        raise ValueError(msg)
    return t[STATE]


def toggleTextsList(i: Iterable) -> None:
    for x in i:
        if isinstance(x, tk.Text):
            # if x is an instance of ScrolledText, it is also an instance of tk.Text
            toggleText(x)


def keepTextDisabled(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwargs) -> Any:
        total = args + tuple(kwargs.values())
        texts = [obj for obj in total if isinstance(obj, tk.Text)]
        # texts = filter(lambda obj: isinstance(obj, tk.Text), total)
        disabled = [t for t in texts if t[STATE] == DISABLED]
        # disabled = list(filter(lambda t: t[STATE] == DISABLED, texts))
        toggleTextsList(disabled)
        output = f(*args, **kwargs)
        toggleTextsList(disabled)
        return output

    return wrapper


@keepTextDisabled
def clear_text(t: tk.Text) -> None:
    t.delete("1.0", tk.END)


@keepTextDisabled
def clear_selected_text(t: tk.Text) -> None:
    try:
        t.delete(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        print("> Nothing selected!")


def select_all(t: tk.Text) -> "break":
    """It's not necessary to protect this with @keepTextDisabled
    """
    t.tag_add(tk.SEL, "1.0", tk.END)
    t.mark_set(tk.INSERT, "1.0")
    t.see(tk.INSERT)
    return "break"


@keepTextDisabled
def typeset_Text(content: str, Text: tk.Text, mode: str = "w") -> str:
    mode = mode.lower()
    if mode not in "aw":
        raise ValueError(f"{mode} should be either w(rite) (default) or a(ppend).")
    size = len(Text.get("1.0", tk.END))
    if mode == "w" or size > 1500:
        clear_text(Text)
        # Text.insert(tk.END, "--cleared--")
        print(f"> {Text} cleared")
    if not content.endswith(EOL):
        content += EOL
    Text.insert(tk.END, content)
    return Text.get("1.0", tk.END)


if __name__ == "__main__":
    print("This module should not be run alone.")
    tk.sys.exit()

_trash = """
Pack a widget in the parent widget. Use as options:
    after=widget - pack it after you have packed widget
    anchor=NSEW (or subset) - position widget according to
                              given direction
    before=widget - pack it before you will pack widget
    expand=bool - expand widget if parent size grows
    fill=NONE or X or Y or BOTH - fill widget if widget grows
    in=master - use master to contain this widget
    in_=master - see 'in' option description
    ipadx=amount - add internal padding in x direction
    ipady=amount - add internal padding in y direction
    padx=amount - add padding in x direction
    pady=amount - add padding in y direction
    side=TOP or BOTTOM or LEFT or RIGHT -  where to add this widget.

wm_grid(self, baseWidth=None, baseHeight=None, widthInc=None, heightInc=None)
    Instruct the window manager that this widget shall only be
    resized on grid boundaries. WIDTHINC and HEIGHTINC are the width and
    height of a grid unit in pixels. BASEWIDTH and BASEHEIGHT are the
    number of grid units requested in Tk_GeometryRequest.
"""
