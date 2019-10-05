#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  setup.py

#from tkinter import sys as tksys
#tksys.path.insert(0, "/home/daniel/Documents/Informática/git/morla/morla")
from setuptools import setup

from morla import *


def readme():
    with open("README.md") as readme_file:
        return readme_file.read()


setup(name = SELETOR_NAME,
      version = SELETOR_VERSION,
      description = "Application to parse and select (La)TeX exercises.",
      url = "https://github.com/dasld/morla",
      author = SELETOR_AUTHOR,
      author_email = SELETOR_EMAIL,
      license = SELETOR_LICENSE,
      packages = ["morla"],
      install_requires = [  # in alphabetical order
          # "base64",
          "configparser",
          "contextlib",
          "functools",
          "idlelib",
          "itertools",
          "io",
          "json",
          "os",
          "setuptools",
          "tkinter",
          "typing"
      ],
      zip_safe = True
)
