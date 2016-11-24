# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

# Import time function
from time import time

# Import for buttons and LED's
import wiringpi

# Imports for OLED display
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Import for Volumio websocket client
from socketIO_client import SocketIO, LoggingNamespace
import json

def volumio_buddy_setup():
    global _volumio_buddy_is_setup
    if not '_volumio_buddy_is_setup' in globals():
        _volumio_buddy_is_setup = True
        wiringpi.wiringPiSetup()
    elif not _volumio_buddy_is_setup == True:
        _volumio_buddy_is_setup = True
        wiringpi.wiringPiSetup()

class PushButton:
    """ Class to register a callback function for a pushbutton """

    def __init__(self, gpio_pin):
        volumio_buddy_setup()
        self.callback_function = False
        self.last_push = 0
        self.minimum_delay = 0.5
        self.gpio_pin = gpio_pin
        wiringpi.pinMode(gpio_pin, 0)

    def set_callback(self, callback_function):
        """ Register a function that is called when the knob is turned """
        self.callback_function = callback_function
        wiringpi.wiringPiISR(self.gpio_pin, wiringpi.INT_EDGE_BOTH, self._callback)

    def _callback(self):
        if time() - self.last_push > self.minimum_delay:
            self.last_push = time()
            self.callback_function()

class RotaryEncoder:
    """ Class to register callback functions for left and right turns on
        a rotary encoder """

    LEFT = 0
    RIGHT = 1

    def __init__(self, gpio_pin_a, gpio_pin_b):
        volumio_buddy_setup()
        self.callback_function = False
        self.in_critical_section = False
        self.prev_state = 0
        self.gpio_pin_a = gpio_pin_a
        self.gpio_pin_b = gpio_pin_b
        wiringpi.pinMode(gpio_pin_a, 0)
        wiringpi.pinMode(gpio_pin_b, 0)

    def set_callback(self, callback_function):
        """ Register a function that is called when the knob is turned """
        self.callback_function = callback_function
        wiringpi.wiringPiISR(self.gpio_pin_a, wiringpi.INT_EDGE_BOTH, self._decode_rotary)
        wiringpi.wiringPiISR(self.gpio_pin_b, wiringpi.INT_EDGE_BOTH, self._decode_rotary)

    def _decode_rotary(self):
        """ Internal class that determines the state of the switches """
        if self.in_critical_section == True or not self.callback_function:
            return
        self.in_critical_section = True
        MSB = wiringpi.digitalRead(self.gpio_pin_a)
        LSB = wiringpi.digitalRead(self.gpio_pin_b)
        new_state = (MSB << 1) | LSB
        sum = (self.prev_state << 2) | new_state
        if(sum == 0b1101 or sum == 0b0100 or sum == 0b0010 or sum == 0b1011):
            self.callback_function(RotaryEncoder.LEFT)
        elif (sum == 0b1110 or sum == 0b0111 or sum == 0b0001 or sum == 0b1000):
            self.callback_function(RotaryEncoder.RIGHT)
        self.prev_state = new_state
        self.in_critical_section = False

class Display:
    """ Class for the user interface using a 164x64 OLED SSD1306 compatible display """

    def __init__(self, reset_pin):
        self.reset_pin = reset_pin
        self._display =  Adafruit_SSD1306.SSD1306_128_64(rst=reset_pin)
        self._display.begin()
        self.width = self._display.width
        self.height = self._display.height
        self.clear()

        self._image = Image.new('1', (self.width, self.height))
        self._draw = ImageDraw.Draw(self._image)

    def image(self, filename):
        """ Show a logo """
        try:
            self._image = Image.open(filename). \
                resize((self.width, self.height), Image.ANTIALIAS).convert('1')
            self._display.image(self._image)
            self._display.display()
        except IOError:
            pass 

    def clear(self):
        """ Clear the display """
        self._display.clear()
        self._display.display()

class VolumioClient:
    """ Class for the websocket client to Volumio """

    def __init__(self):
        HOSTNAME='localhost'
        PORT=3000

        self._callback = False

        def _on_pushState(*args):
            self.state = args[0]
            if self._callback:
                self._callback(self.state)

        self._client = SocketIO(HOSTNAME, PORT, LoggingNamespace)
        self._client.on('pushState', _on_pushState)
        self._client.emit('getState', _on_pushState)
        self._client.wait_for_callbacks(seconds=1)

    def set_callback(self, callback):
        self._callback = callback

    def play(self):
        self._client.emit('play')

    def pause(self):
        self._client.emit('pause')

    def toggle_play(self):
        try:
            if self.state["status"] == "play":
                self._client.emit('pause')
            else:
                self._client.emit('play')
        except KeyError:
            self._client.emit('play')

    def volume_up(self):
        self._client.emit('volume', '+')

    def volume_down(self):
        self._client.emit('volume', '-')
               
    def wait(self):
        self._client.wait()

