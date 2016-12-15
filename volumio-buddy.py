#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import sys
from time import time
sys.path.append("/home/volumio/volumio-buddy/volumio_buddy")
from volumio_buddy import PushButton, RotaryEncoder, RGBLED, VolumioClient, Display

def update_volume(direction, client):
    if time() - client.last_update_time > .1:
        client.last_update_time = time()
        if direction == RotaryEncoder.LEFT:
            client.volume_down()
            print "volume down"
        elif direction == RotaryEncoder.RIGHT:
            client.volume_up()
            print "volume up"
        else:
            print "unknown rotary encoder event"

def previous_next(direction, client):
    if time() - client.last_update_time > 1:
        client.last_update_time = time()
        if direction == RotaryEncoder.LEFT:
            client.previous()
            print "previous song"
        elif direction == RotaryEncoder.RIGHT:
            client.next()
            print "next song"
        else:
            print "unknown rotary encoder event"

def toggle_play(client):
    client.toggle_play()
    print "play / pause"

def print_state(client, display, led):
    try:
        duration =  int(client.state["duration"])
    except TypeError:
        duration = 0
    except KeyError:
        duration = 0
    try:
        seek =  int(int(client.state["seek"])/1000)
    except KeyError:
        seek = 0
    except TypeError:
        seek = 0
    try:
        artist=  client.state["artist"] + " - "
    except KeyError:
        artist = ""
    except TypeError:
        artist = ""
    try:
        album=  client.state["album"] + " - "
    except KeyError:
        album = ""
    except TypeError:
        album = ""
    try:
        title=  client.state["title"]
    except KeyError:
        title = ""
    display.update_main_screen(artist + album + title, duration, seek)
    last_volume = int(client.prev_state["volume"])
    print "status: " + str(client.state["status"])
    print "seek: " + str(client.state["seek"])
    print "volume: " + str(int(client.state["volume"]))
    if client.state["volume"] <> client.prev_state["volume"]:
        display.volume_modal(int(client.state["volume"]), 3)
    elif client.state["status"] <> client.prev_state["status"]:
        if client.state["status"] == "play":
            display.status(Display.STATUS_PLAY, 3)
            led.set(0, 10, 0)
        elif client.state["status"] == "pause":
            display.status(Display.STATUS_PAUSE, 3)
            led.set(10, 0, 0)
        elif client.state["status"] == "stop":
            display.status(Display.STATUS_STOP, 3)
            led.set(0, 0, 10)

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
display.image("volumio.ppm")

client=VolumioClient()
client.set_callback(print_state, client, display, led)

push_button = PushButton(PB1)
push_button.set_callback(toggle_play, client)

rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B)
rotary_encoder.set_callback(update_volume, client)

push_button2 = PushButton(PB2)
push_button2.set_callback(show_menu, display)

rotary_encoder2 = RotaryEncoder(ROT_ENC_2A, ROT_ENC_2B)
rotary_encoder2.set_callback(previous_next, client)

# Wait for event from either one of the buttons or the websocket connection
client.wait()
