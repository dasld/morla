#!/bin/bash

pyinstaller setup.py -n morla --onefile --windowed --clean --icon=data/logo.ico
mv dist/morla ./morla-bin
rm -R build/ dist/
rm morla.spec
