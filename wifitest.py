#!/usr/bin/python
from __future__ import print_function

from wifi import Cell, Scheme


ssids = [cell.ssid for cell in Cell.all('wlan0')]
print(ssids[0])