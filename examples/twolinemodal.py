#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from sys import argv
from random import randrange
from volumio_buddy import Display

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
        display.volume_modal(randrange(100), 3)
        time.sleep(10)
        display.volume_modal(randrange(100), 3)
finally:
# clear screen before exiting
    display.clear()
