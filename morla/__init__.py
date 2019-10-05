#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# % UFPR-PR 2014
# % Uso: lista01 2023
# lorem ipsum.

# \begin{choices}
# \choice foo
# \CorrectChoice bar
# \end{choices}


# from tkinter import sys as tksys
# import os
# from contextlib import redirect_stdout
# from typing import Any

from morla.morlaframe import gui_loop


SELETOR_NAME = "Morla"
SELETOR_VERSION = (0, 1)
VERBOSE = True
SELETOR_AUTHOR = "Daniel Alves da Silva Lopes Diniz"
SELETOR_EMAIL = "diniz.cpm<at>gmail.com"
SELETOR_LICENSE = "GNU Affero General Public License v3 or later (AGPLv3+)"


# main loop
gui_loop()


if __name__ == "__main__":
    print("This module should not be run alone.")
    from tkinter import sys

    sys.exit()
