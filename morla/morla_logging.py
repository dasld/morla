# -*- coding: utf-8 -*-

# from typing import Any, Callable, List, Iterable, Optional, Union, Tuple

# sys is already loaded by tkinter; see below
#import io
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging

# import base64
# from functools import partial, wraps
# import json

# import webbrowser as browser

# from tkinter import sys
import tkinter as tk

from morla.utils import *  # why doesn't morla.utils import SELETOR_NAME work?

# from morla.configuration import Configuration
# from morla.preference import Preferences
# from morla.bulk import Parser
from morla.gui import keepTextDisabled
# from morla.tooltip import Tooltip
from morla import *  # SELETOR_NAME

# import morla


class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget.
    https://beenje.github.io/blog/posts/logging-to-a-tkinter-scrolledtext-widget/
    """

    def __init__(self, text: tk.Text):
        # run the regular Handler __init__
        #logging.Handler.__init__(self)
        super(TextHandler, self).__init__()
        # store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        if not msg.endswith(EOL):
            msg += EOL

        # why doesn't @keepTextDisabled work here?
        def append():
            self.text.configure(state = "normal")
            self.text.insert(tk.END, msg)
            self.text.configure(state = "disabled")
            # autoscroll to the bottom
            self.text.yview(tk.END)
        # this is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


def init_logger(filename: str, Text: tk.Text) -> logging.Logger:
    # file handler which logs everything
    fh = logging.FileHandler(filename, encoding=UTF8, mode="w")
    fh.setLevel(DEBUG)
    # text handler wich logs INFOs and above
    txt = TextHandler(Text)
    txt.setLevel(INFO)
    # console handler which logs only ERRORs and CRITICALs
    cmd = logging.StreamHandler()
    cmd.setLevel(ERROR)
    # formatter for all handlers
    date = "%d-%m %H:%M"
    levelwidth = len(logging.getLevelName(CRITICAL))
    levelname = f"%(levelname)-{levelwidth}s"
    fmt = f"[{levelname}] %(message)s"
    formatter = logging.Formatter(fmt, datefmt=date)
    # ("%(name)-12s: %(levelname)-8s %(message)s")
    fh.setFormatter(formatter)
    txt.setFormatter(formatter)
    cmd.setFormatter(formatter)
    # create the root logger
    logging.basicConfig(
        handlers=(fh, txt, cmd),
        # format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        # format="%(levelname)-8s %(message)s",
        # datefmt="%d-%m %H:%M",
        level=DEBUG,
        # filemode="w",
    )
    return logging.getLogger()


if __name__ == "__main__":
    from tkinter import sys

    sys.exit("This module should not be run alone.")
