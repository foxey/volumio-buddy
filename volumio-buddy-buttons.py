#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import sys
from time import time
from os import path
from volumio_buddy import __file__ as filename
from volumio_buddy import PushButton, RotaryEncoder, RGBLED, VolumioClient, Display
from wiringpi import delay

def update_volume(rotary_encoder, client):
    if time() - client.last_update_time > .1:
        client.last_update_time = time()
        if rotary_encoder.direction == RotaryEncoder.LEFT:
            client.volume_down()
            print "volume down"
        elif rotary_encoder.direction == RotaryEncoder.RIGHT:
            client.volume_up()
            print "volume up"
        else:
            print "unknown rotary encoder event"

def previous_next(rotary_encoder, client):
    if time() - client.last_update_time > 1:
        client.last_update_time = time()
        if rotary_encoder.direction == RotaryEncoder.LEFT:
            client.previous()
            print "previous song"
        elif rotary_encoder.direction == RotaryEncoder.RIGHT:
            client.next()
            print "next song"
        else:
            print "unknown rotary encoder event"

def toggle_play(client):
    try:
        if client.state["status"] == "play":
            client.state["status"] = "pause"
            print "pause"
        else:
            client.state["status"] = "play"
            print "play"
    except NameError, KeyError:
        client.state["status"] = "pause"
        print "pause (exception)"
    client.toggle_play()

# Rotary encoder 1 pins (WiringPi numbering)
PB1 = 0
ROT_ENC_1A = 2
ROT_ENC_1B = 21

# Rotary encoder 2 pins (WiringPi numbering)
PB2 = 7
ROT_ENC_2A = 4
ROT_ENC_2B = 5

# LED pins (WiringPi numbering)
LED_RED = 23
LED_GREEN = 26
LED_BLUE = 22

# SSD3106 reset pin (not used)
RESET_PIN = 26

push_button = PushButton(PB1)
push_button2 = PushButton(PB2)
rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder2 = RotaryEncoder(ROT_ENC_2A, ROT_ENC_2B)

client=VolumioClient()

push_button.set_callback(toggle_play, client)
push_button2.set_callback(toggle_play, client)

rotary_encoder.set_callback(update_volume, rotary_encoder, client)
rotary_encoder2.set_callback(previous_next, rotary_encoder2, client)

# Wait for event from either one of the buttons
while True:
    delay(2000)
