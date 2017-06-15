#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from os import path, fork
from volumio_buddy import __file__ as filename
from volumio_buddy import PushButton, RotaryEncoder, RGBLED, VolumioClient, Display, PipeWriter

from wiringpi import delay

def update_volume(rotary_encoder, pipe):
    if rotary_encoder.direction == RotaryEncoder.LEFT:
        pipe.write("volume_down")
    elif rotary_encoder.direction == RotaryEncoder.RIGHT:
        pipe.write("volume_up")
    else:
        print "unknown rotary encoder event"

def previous_next(rotary_encoder, pipe):
    if rotary_encoder.direction == RotaryEncoder.LEFT:
        pipe.write("previous_song")
    elif rotary_encoder.direction == RotaryEncoder.RIGHT:
        pipe.write("next_song")
    else:
        print "unknown rotary encoder event"

def toggle_play(pipe):
    pipe.write("toggle_play")

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

def show_menu(pipe):
    pipe.write('show_menu')

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

pipe = PipeWriter()

if fork() != 0:
    pipe.close(PipeWriter.OUT)
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

# Wait for events from the websocket connection in separate thread
        client.wait()
        while True:
            print 'waiting for command'
            command = '%s' % pipe.read()
            print 'recieved command: %s' % command
            if command == 'volume_up':
                client.volume_up()
            elif command == 'volume_down':
                client.volume_down()
            elif command == 'next_song':
                client.next()
            elif command == 'previous_song':
                client.previous()
            elif command == 'toggle_play':
                client.toggle_play()
            elif command == 'show_menu':
# Display the menu modal for 3 sec
                display.menu(3)
            else:
                print "unknown command"

else:
    pipe.close(PipeWriter.IN)
    push_button = PushButton(PB1)
    push_button2 = PushButton(PB2)
    rotary_encoder = RotaryEncoder(ROT_ENC_1A, ROT_ENC_1B, minimum_delay=0.1)
    rotary_encoder2 = RotaryEncoder(ROT_ENC_2A, ROT_ENC_2B)

    push_button.set_callback(toggle_play, pipe)
    push_button2.set_callback(show_menu, pipe)

    rotary_encoder.set_callback(update_volume, rotary_encoder, pipe)
    rotary_encoder2.set_callback(previous_next, rotary_encoder2, pipe)

    while True:
        delay(2000)
