#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import sys
from time import time
from os import path
from volumio_buddy import __file__ as filename
from volumio_buddy import RGBLED, VolumioClient, Display

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
    client.toggle_play()
    print "play / pause"

def print_state(client, display, led):
# Tedious input sanitation
    try:
        duration =  int(client.state["duration"])
    except (ValueError, TypeError, KeyError):
        duration = 0
    try:
        seek =  int(int(client.state["seek"])/1000)
    except (ValueError, TypeError, KeyError):
        seek = 0
    try:
        artist=  client.state["artist"] + " - "
    except (TypeError, KeyError):
        artist = ""
    try:
        album=  client.state["album"] + " - "
    except (TypeError, KeyError):
        album = ""
    try:
        title =  client.state["title"]
    except KeyError:
        title = ""
    try:
        status =  client.state["status"]
    except KeyError:
        status = ""
    try:
        prev_status =  client.prev_state["status"]
    except KeyError:
        status = ""
    try:
        volume =  int(client.state["volume"])
    except (ValueError, TypeError, KeyError):
        volume = 0
    try:
        prev_volume = int(client.prev_state["volume"])
    except (ValueError, TypeError, KeyError):
        prev_volume = 0

# Update the data for the main screen
    display.update_main_screen(artist + album + title, duration, seek)

# Show volume modal if the volume changed
    if volume <> prev_volume:
        display.volume(volume, 3)
# Show status modal & change LED colour if the status changed (between play, pause & stop)
    elif status <> prev_status:
        if status == "play":
            display.status(Display.STATUS_PLAY, 3)
            led.set(0, 10, 0)
        elif status == "pause":
            display.status(Display.STATUS_PAUSE, 3)
            led.set(10, 0, 0)
        elif status == "stop":
            display.status(Display.STATUS_STOP, 3)
            led.set(0, 0, 10)

# Debug information
    print "status: " + status
    print "seek: " + str(seek)
    print "volume: " + str(volume)

def show_menu(display):
# Display the menu modal for 3 sec
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
display.image(path.dirname(path.realpath(filename)) + "/volumio.ppm")
display.start_updates()

while True:
# Ensure client restarts after network disconnection
    print "start websocket connection"
    client=VolumioClient()
    client.set_callback(print_state, client, display, led)
# Wait for event from either one of the buttons or the websocket connection
    client.wait()
    print "lost websocket connection"
