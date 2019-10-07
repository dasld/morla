# -*- coding: utf-8 -*-

from typing import Any, Optional

# sys is already loaded by tkinter; use tk.sys instead
import os

from configparser import ConfigParser

from tkinter import sys
import tkinter as tk

from morla.utils import *
from morla.gui import ENABLED, DISABLED


class Preferences(ConfigParser):
    defaults = {"language": ENUS, "tooltip": "True"}  # only strings as values!

    synonyms = {True: set(("true", ENABLED)), False: set(("false", DISABLED))}

    def __init__(self, directory: str, D: Optional[dict] = None) -> None:
        super(Preferences, self).__init__()
        self.directory = os.path.expanduser(directory)
        print("> Preferences object at", self.directory)
        if D:
            illegal = dict_diff(D, self.defaults)
            if illegal:
                illegal = COMMA.join(sorted(illegal))
                raise ValueError(f"{illegal} are not valid preference keys.")
            self[DEFAULT] = D.copy()
        else:
            self[DEFAULT] = self.defaults.copy()

    def get_section(self) -> str:
        try:
            return self[USER]
        except KeyError:
            return self[DEFAULT]

    def set_user_pref(self, key: str, value: Any) -> None:
        try:
            self[USER]
        except KeyError:
            self[USER] = {}
        if not isinstance(value, str):
            try:
                value = str(value)
            except ValueError:
                print(f"> couldn't convert {value} to str!")
                raise
            else:
                print(f"> converting {value} to str...")
        self[USER][key] = value

    def save(self, name: str = "preferences", where: str = None):
        if not where:
            where = self.directory
        with Cd(where):
            filename = name + ".ini"
            with open(filename, "w") as prefs_file:
                try:
                    self.write(prefs_file)
                    # json.dump(self.dict, json_file)
                except:
                    print(f"> Writing {filename} failed.")
                    raise
                else:
                    print(f"> Wrote {filename}.")
            print_sep()
            with open(filename, "r") as prefs_file:
                print(prefs_file.read().strip())
            print_sep()


if __name__ == "__main__":
    sys.exit("This module should not be run alone.")
