#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

from volumio_buddy import VolumioClient

def print_state(client):
    print client.state

client=VolumioClient()
client.set_callback(print_state, client)
client.wait()
