#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import sys
from time import time
sys.path.append("/home/volumio/volumio-buddy/volumio_buddy")
from volumio_buddy import PushButton, RotaryEncoder, RGBLED, VolumioClient, Display

def update_volume(d):
    global client
    if d == RotaryEncoder.LEFT:
        client.volume_down()
    elif d == RotaryEncoder.RIGHT:
        client.volume_up()
    else:
        print "unknown rotary encoder event"

def previous_next(d):
    global client
    global rotary_encoder2_time 
    if time() - rotary_encoder2_time > 1:
        if d == RotaryEncoder.LEFT:
            rotary_encoder2_time = time()
            client.previous()
        elif d == RotaryEncoder.RIGHT:
            rotary_encoder2_time = time()
            client.next()
        else:
            print "unknown rotary encoder event"

def toggle_play():
    global client
    client.toggle_play()

def print_state(prev_state, state):
    global display
    global led
    try:
        seek =  int(int(state["seek"])/1000)
    except TypeError:
        seek = 0
    display.update_main_screen(state["artist"] + " - " + state["album"] + " - " +
            state["title"], int(state["duration"]), seek)
    last_volume = int(prev_state["volume"])
    print "status: " + str(state["status"])
    print "seek: " + str(state["seek"])
    print "volume: " + str(int(state["volume"]))
    if state["volume"] <> prev_state["volume"]:
        display.volume_modal(int(state["volume"]), 3)
    elif state["status"] <> prev_state["status"]:
        if state["status"] == "play":
            display.status(Display.STATUS_PLAY, 3)
            led.set(0, 10, 0)
        elif state["status"] == "pause":
            display.status(Display.STATUS_PAUSE, 3)
            led.set(10, 0, 0)
        elif state["status"] == "stop":
            display.status(Display.STATUS_STOP, 3)
            led.set(0, 0, 10)

def show_menu():
    global display
    display.menu(3)

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

led = RGBLED(LED_RED, LED_GREEN, LED_BLUE)
led.set(0, 0, 10)

display = Display(RESET_PIN)
display.image("volumio.ppm")

client=VolumioClient()
client.set_callback(print_state)

push_button = PushButton(PB1)
push_button.set_callback(toggle_play)

rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder.set_callback(update_volume)

push_button2 = PushButton(PB2)
push_button2.set_callback(show_menu)

rotary_encoder2 = RotaryEncoder(ROT_ENC_2A, ROT_ENC_2B)
rotary_encoder2.set_callback(previous_next)

rotary_encoder2_time = 0

client.wait()
