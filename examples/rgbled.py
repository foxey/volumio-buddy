#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from time import sleep
from volumio_buddy import RGBLED

PIN_R = 23
PIN_G = 26
PIN_B = 22

led = RGBLED(PIN_R, PIN_G, PIN_B)

for red in range(101):
    led.set(red, 0, 0)
    sleep(.1)
for red in range(100,-1,-1):
    led.set(red, 0, 0)
    sleep(.1)
for green in range(101):
    led.set(0, green, 0)
    sleep(.1)
for green in range(100,-1,-1):
    led.set(0, green, 0)
    sleep(.1)
for blue in range(101):
    led.set(0, 0, blue)
    sleep(.1)
for blue in range(100, -1, -1):
    led.set(0, 0, blue)
    sleep(.1)
