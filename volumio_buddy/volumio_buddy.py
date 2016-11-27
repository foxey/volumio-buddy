# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

# Import time function
from time import time, sleep

# Import thread library for modal timeout handling
import thread

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

    LEFT = 1
    RIGHT = 2

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

class RGBLED:
    """ Class to drive an RGB LED with soft PWM """

    def __init__(self, gpio_pin_r, gpio_pin_g, gpio_pin_b):
        volumio_buddy_setup()
        self.gpio_pin_r = gpio_pin_r
        self.gpio_pin_g = gpio_pin_g
        self.gpio_pin_b = gpio_pin_b
        self.r_value = 0
        self.g_value = 0
        self.b_value = 0
        wiringpi.pinMode(gpio_pin_r, 1)
        wiringpi.pinMode(gpio_pin_g, 1)
        wiringpi.pinMode(gpio_pin_b, 1)
        wiringpi.softPwmCreate(gpio_pin_r, 0, 100)
        wiringpi.softPwmCreate(gpio_pin_g, 0, 100)
        wiringpi.softPwmCreate(gpio_pin_b, 0, 100)

    def set(self, r_value, g_value, b_value):
        self.r_value = r_value
        self.g_value = g_value
        self.b_value = b_value
        wiringpi.softPwmWrite(self.gpio_pin_r, r_value)
        wiringpi.softPwmWrite(self.gpio_pin_g, g_value)
        wiringpi.softPwmWrite(self.gpio_pin_b, b_value)

    def get(self):
        return (self.r_value, self.g_value, self.b_value)

class Display:
    """ Class for the user interface using a 164x64 OLED SSD1306 compatible display """

# Text modal type definitions
    MODAL_PLAY = 1
    MODAL_PAUSE = 2
    MODAL_STOP = 3
# Text label definitions
    TXT_VOLUME = "Volume"
    TXT_PLAY = "Play"
    TXT_PAUSE = "Pause"
    TXT_STOP = "Stop"

    def __init__(self, reset_pin):
        self.reset_pin = reset_pin
        self._display =  Adafruit_SSD1306.SSD1306_128_64(rst=reset_pin)
        self._modal_timeout = 0
        self._dirty = False
        self._display.begin()
        self.width = self._display.width
        self.height = self._display.height

# Define image and draw objects for main screen and modal screen
        self._image = Image.new('1', (self.width, self.height))
        self._draw = ImageDraw.Draw(self._image)

        self.clear()

        self._modal_image = Image.new('1', (self.width, self.height))
        self._modal_draw = ImageDraw.Draw(self._image)

# Load font. If TTF file is not found, load default font
# Make sure the .ttf font file is in the same directory as
# the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
        try:
            self._font = ImageFont.truetype('pixChicago.ttf', 10)
        except:
            self._font = ImageFont.load_default()

# Start thread that will update the screen regulary
        thread.start_new_thread(self._update, ())

# Lock thread during image update to prevent image distortion`
    def display(self, image):
        """ Update display with new image """
        wiringpi.piLock(0)
        self._display.image(image)
        self._display.display()
        wiringpi.piUnlock(0)

    def image(self, filename):
        """ Show a logo """
        try:
            self._image = Image.open(filename). \
                resize((self.width, self.height), Image.ANTIALIAS).convert('1')
            self.display(self._image)
        except IOError:
            print "Cannot open file %s" % filename
            pass 

    def _update(self):
        """ Clear the display """
        next_update_time = 0
        while True:
            if time()-next_update_time > 0:
                next_update_time = time()+1
                if (time()-self._modal_timeout) > 0:
                    self.display(self._image)
            sleep(.25)

    def clear(self):
        """ Clear the display """
        self._draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.display(self._image)

    def volume_modal(self, level, delay):
        """ Pop-up window with slider bar for volume """
        textlabel = Display.TXT_VOLUME + ' ' + str(int(level))
        self.display(BarModal(self._image, self._font, textlabel, level).image())
        self._modal_timeout = time() + delay

    def text_modal(self, modal_type, delay):
        """ Pop-up window with horizontally and vertically centered text label """
        if modal_type == Display.MODAL_PLAY:
            textlabel = Display.TXT_PLAY
        elif modal_type == Display.MODAL_PAUSE:
            textlabel = Display.TXT_PAUSE
        elif modal_type == Display.MODAL_STOP:
            textlabel = Display.TXT_STOP
        else:
            textlabel = "Huh?"
        self.display(TextModal(self._image, self._font, textlabel).image())
        self._modal_timeout = time() + delay

class TextModal:
    """ Class that creates a modal with a textlabel """

    def __init__(self, image, font, textlabel):

        self._image = image.copy()
        (image_width, image_height) = self._image.size
        self._draw = ImageDraw.Draw(self._image)

        x = 4
        y_fraction = 0.2
        y = int(y_fraction*image_height)

        width = image_width - 2*x 
        height = image_height - 2*y
        x_padding = 8
        y_padding = 8
        bar_height = 6

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = x+int((width-textwidth)/2)
        ytext = y+int((height-textheight)/2)

        self._draw.rectangle((x, y, x+width, y+height), outline=1, fill=0)
        self._draw.text((xtext, ytext), textlabel, font=font, fill=255)

    def image(self):
        return self._image

class BarModal:
    """ Class that creates a modal with a label and a sliderbar"""

    def __init__(self, image, font, textlabel, level):

        self._image = image.copy()
        (image_width, image_height) = self._image.size
        self._draw = ImageDraw.Draw(self._image)

        x = 4
        y_fraction = 0.2
        y = int(y_fraction*image_height)

        width = image_width - 2*x 
        height = image_height - 2*y

        x_padding = 8
        y_padding = 8
        bar_height = 6

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = x+int((width-textwidth)/2)
        ytext = y+4

        self._draw.rectangle((x, y, x+width, y+height), outline=1, fill=0)
        self._draw.rectangle((x+x_padding, y+height-y_padding-bar_height, \
                       x+width-x_padding, y+height-y_padding), outline=1, fill=0)
        self._draw.rectangle((x+x_padding, y+height-y_padding-bar_height, \
                       x+int(width*level/100)-x_padding, y+height-y_padding), outline=1, fill=1)
        self._draw.text((xtext, ytext), textlabel, font=font, fill=255)

    def image(self):
        return self._image

class VolumioClient:
    """ Class for the websocket client to Volumio """

    def __init__(self):
        HOSTNAME='localhost'
        PORT=3000

        self._callback = False
        self.prev_state = False

        def _on_pushState(*args):
            self.state = args[0]
            if not self.prev_state:
                self.prev_state = self.state
            if self._callback:
                self._callback(self.prev_state, self.state)
            self.prev_state = self.state

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

