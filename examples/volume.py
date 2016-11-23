#!/usr./bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from volumio_buddy import RotaryEncoder, VolumioClient

def update_volume(d):
    global client
    if d == RotaryEncoder.LEFT:
        client.volume_down()
    elif d == RotaryEncoder.RIGHT:
        client.volume_up()
    else:
        print "unknown rotary encoder event"

def print_volume(state):
    print "volume: " + str(state["volume"])

ROT_ENC_1A = 2
ROT_ENC_1B = 21

client=VolumioClient()
client.set_callback(print_volume)

rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder.set_callback(update_volume)

client.wait()
