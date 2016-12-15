#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from sys import argv
from random import randrange
from volumio_buddy import Display, TwoLineTextModal

RESET_PIN = 26

display = Display(RESET_PIN)

if len(argv) > 1:
    display.image(argv[1])
else:
    display.image("volumio.ppm")

import time

try:
# wait until ^C pressed
    while True:
        textlabel=('text line 1', 'text line 2')
        display._modal_timeout = time.time() + 3
        display.display(TwoLineTextModal(display._image, display._modal_font, textlabel).image())
        time.sleep(10)
        textlabel=('more text 3', 'more text 4')
        display._modal_timeout = time.time() + 5
        display.display(TwoLineTextModal(display._image, display._modal_font, textlabel).image())
        time.sleep(3)
        textlabel=('line 5', 'line 6')
        display._modal_timeout = time.time() + 3
        display.display(TwoLineTextModal(display._image, display._modal_font, textlabel).image())
        time.sleep(5)
finally:
# clear screen before exiting
    display.clear()
