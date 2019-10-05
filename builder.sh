#!/bin/bash

pyinstaller setup.py -n morla --onefile --windowed
mv dist/morla ./morla-bin
rm -R build/ dist/
