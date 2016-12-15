#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from volumio_buddy import PushButton, VolumioClient

def toggle_play(client):
    client.toggle_play()

def print_state(client):
    print "status: " + str(client.state["status"])
    print "volume: " + str(client.state["volume"])

PIN = 0

client=VolumioClient()
client.set_callback(print_state, client)

push_button = PushButton(PIN)
push_button.set_callback(toggle_play, client)

client.wait()
