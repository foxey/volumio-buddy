#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from os import path, fork
import subprocess
from volumio_buddy import __file__ as filename
from volumio_buddy import PushButton, RotaryEncoder, RGBLED, VolumioClient, Display, PipeWriter, Network, Battery

from wiringpi import delay

def update_volume(rotary_encoder, pipe):
    if rotary_encoder.direction == RotaryEncoder.LEFT:
        pipe.write("volume_down")
    elif rotary_encoder.direction == RotaryEncoder.RIGHT:
        pipe.write("volume_up")
    else:
        print("unknown rotary encoder event")

def previous_next(rotary_encoder, pipe):
    if rotary_encoder.direction == RotaryEncoder.LEFT:
        pipe.write("previous_song")
    elif rotary_encoder.direction == RotaryEncoder.RIGHT:
        pipe.write("next_song")
    else:
        print("unknown rotary encoder event")

def toggle_play(pipe):
    pipe.write("toggle_play")

def show_menu(pipe):
    pipe.write('show_menu')

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
        display.volume(volume)
# Update display status & change LED colour
    if status == "play":
        display.status(Display.STATUS_PLAY)
        led.set(0, 10, 0)
    elif status == "pause":
        display.status(Display.STATUS_PAUSE)
        led.set(0, 0, 10)
    elif status == "stop":
        display.status(Display.STATUS_STOP)
        led.set(0, 0, 10)

# Debug information
    try:
        print("")
        print("status: " + str(status))
        print("song: " + artist.encode('utf-8') + album.encode('utf-8') + title.encode('utf-8'))
        print("duration: " + str(duration))
        print("seek: " + str(seek))
        print("volume: " + str(volume))
        print("")
    except Exception as e:
        print("encountered " + str(type(e)) + " exception.")
        print(e.args)

def low_battery_warning(led):
    led.set(10, 0, 0)

def empty_battery():
    subprocess.call(["/sbin/shutdown", "now"])

class BatteryMenuItem(object):
    TXT_LEVEL = "Battery"
    TXT_VOLTAGE = "Voltage"
    def __init__(self):
        self._battery = Battery()
    def textlabel(self):
        textlabel = (BatteryMenuItem.TXT_LEVEL+ ": %d%%" % self._battery.level(), \
                        BatteryMenuItem.TXT_VOLTAGE+ ": %.2f V" % self._battery.voltage())
        return textlabel

class IPMenuItem(object):
    TXT_SSID = "ssid"
    TXT_IP = "ip"
    TXT_NONE = "none"
    def __init__(self):
        self._network = Network()
    def textlabel(self):
        my_ip = self._network.my_ip() or IPMenuItem.TXT_NONE
        textlabel = (IPMenuItem.TXT_SSID + ": " + str(self._network.wpa_supplicant["ssid"]), \
                        IPMenuItem.TXT_IP + ": " + str(my_ip))
        return textlabel
        

class HotspotMenuItem(object):
    TXT_SSID = "ssid"
    TXT_PASSWORD = "pw"
    def __init__(self):
        self._network = Network()
    def textlabel(self):
        textlabel = (HotspotMenuItem.TXT_SSID + ": " + str(self._network.hostapd["ssid"]), \
                        HotspotMenuItem.TXT_PASSWORD + ": " + self._network.hostapd["wpa_passphrase"])
        return textlabel
        

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

    battery=Battery()
    battery.set_warn_function(low_battery_warning, led)
    battery.set_empty_function(empty_battery)
    battery.start_monitor()

    display = Display(RESET_PIN)
    display.image(path.dirname(path.realpath(filename)) + "/volumio.ppm")
    display.set_modal_duration(3)
    menu_items = []
    menu_items.append(BatteryMenuItem())
    menu_items.append(IPMenuItem())
    menu_items.append(HotspotMenuItem())
    display.set_menu_items(menu_items)
    display.start_updates()

    while True:
# Ensure client restarts after network disconnection
        print("start websocket connection")
        client=VolumioClient()
        client.set_callback(print_state, client, display, led)

# Wait for events from the websocket connection in separate thread
        client.wait()
        while True:
            print('waiting for command')
            command = '%s' % pipe.read()
            print('recieved command: %s' % command)
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
# Display the menu modal
                display.menu()
            else:
                print("unknown command")

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
