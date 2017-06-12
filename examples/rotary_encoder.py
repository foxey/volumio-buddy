#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from volumio_buddy import RotaryEncoder
import wiringpi

def print_direction(rotary_encoder):
    if rotary_encoder.direction == RotaryEncoder.LEFT:
        print "direction: left"
    elif rotary_encoder.direction == RotaryEncoder.RIGHT:
        print "direction: right"
    else:
        print "direction: unknown (%s)" % rotary_encoder.direction

ROT_ENC_1A = 2
ROT_ENC_1B = 21
ROT_ENC_2A = 4
ROT_ENC_2B = 5

rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder.set_callback(print_direction, rotary_encoder)

rotary_encoder2 = RotaryEncoder(ROT_ENC_2A, ROT_ENC_2B)
rotary_encoder2.set_callback(print_direction, rotary_encoder)

while True:
    wiringpi.delay(2000)
    
