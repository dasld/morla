# -*- coding: utf-8 -*-

from typing import Any, Optional

# sys is already loaded by tkinter; use tk.sys instead
# import os

import tkinter as tk

# https://github.com/python/cpython/blob/3.6/Lib/idlelib/tooltip.py
from idlelib.tooltip import Hovertip

from morla.utils import *


class Tooltip(Hovertip):
    """Create a text tooltip with a mouse hover delay.
    anchor_widget: the widget next to which the tooltip will be shown
    hover_delay: time to delay before showing the tooltip, in milliseconds
    Note that a widget will only be shown when showtip() is called, e.g. after hovering
    over the anchor widget with the mouse for enough time.
    idlelib.tooltip.Hovertip:
    https://github.com/python/cpython/blob/f1f9c0c532089824791cfc18e6d6f29e1cd62596/Lib/idlelib/tooltip.py#L145
    """

    def __init__(self, anchor_widget, text, hover_delay=500):
        # Hovertip's __init__: (self, anchor_widget, text, hover_delay=1000)
        super(Tooltip, self).__init__(anchor_widget, text, hover_delay=hover_delay)
        pass


if __name__ == "__main__":
    print("This module should not be run alone.")
    tk.sys.exit()
