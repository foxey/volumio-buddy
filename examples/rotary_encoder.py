#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from volumio_buddy import RotaryEncoder

def print_direction(d):
    if d == RotaryEncoder.LEFT:
        print "left"
    elif d == RotaryEncoder.RIGHT:
        print "right"
    else:
        print "unknown"

ROT_ENC_1A = 2
ROT_ENC_1B = 21
ROT_ENC_2A = 4
ROT_ENC_2B = 5

rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder.set_callback(print_direction)

rotary_encoder2 = RotaryEncoder(ROT_ENC_2A, ROT_ENC_2B)
rotary_encoder2.set_callback(print_direction)

while True:
    pass
