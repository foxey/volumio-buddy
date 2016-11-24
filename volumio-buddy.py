#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import sys
sys.path.append("/home/volumio/volumio-buddy/volumio_buddy")
from volumio_buddy import PushButton, RotaryEncoder, VolumioClient, Display

def update_volume(d):
    global client
    if d == RotaryEncoder.LEFT:
        client.volume_down()
    elif d == RotaryEncoder.RIGHT:
        client.volume_up()
    else:
        print "unknown rotary encoder event"

def toggle_play():
    global client
    client.toggle_play()

def print_state(state):
    print "status: " + str(state["status"])
    print "volume: " + str(state["volume"])

PB1 = 0
ROT_ENC_1A = 2
ROT_ENC_1B = 21
RESET_PIN = 26

display = Display(RESET_PIN)
display.image("volumio.ppm")

client=VolumioClient()
client.set_callback(print_state)

push_button = PushButton(PB1)
push_button.set_callback(toggle_play)

rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder.set_callback(update_volume)

client.wait()
