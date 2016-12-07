# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

# Import time functions
from time import time, sleep

# Import thread library for modal timeout handling
import thread


# Import network library
import socket

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
    """ Setup WiringPi and ensure that it is only executed once """
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

#              +---------+         +---------+      0
#              |         |         |         |
#    A         |         |         |         |
#              |         |         |         |
#    +---------+         +---------+         +----- 1
# 
#        +---------+         +---------+            0
#        |         |         |         |
#    B   |         |         |         |
#        |         |         |         |
#    ----+         +---------+         +---------+  1

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
        """ Set the values of each color to 0-100 """
        self.r_value = r_value
        self.g_value = g_value
        self.b_value = b_value
        wiringpi.softPwmWrite(self.gpio_pin_r, r_value)
        wiringpi.softPwmWrite(self.gpio_pin_g, g_value)
        wiringpi.softPwmWrite(self.gpio_pin_b, b_value)

    def get(self):
        """ Get the values of each color """
        return (self.r_value, self.g_value, self.b_value)

class Display:
    """ Class for the user interface using a 164x64 OLED SSD1306 compatible display """

# Text modal type definitions
    STATUS_PLAY = 1
    STATUS_PAUSE = 2
    STATUS_STOP = 3
# Text label definitions
    TXT_VOLUME = "Volume"
    TXT_PLAY = "Play"
    TXT_PAUSE = "Pause"
    TXT_STOP = "Stop"

    MENU_ITEMS = 2
    MENU_NETWORK = 1
    MENU_WIFI = 2

    def __init__(self, reset_pin):
        self.reset_pin = reset_pin
        self._display =  Adafruit_SSD1306.SSD1306_128_64(rst=reset_pin)
        self._status = Display.STATUS_STOP
        self._label = ""
        self._prev_label = ""
        self._duration = 0
        self._seek = 0
        self._main_screen_last_updated = 0
        self._modal_timeout = 0
        self._menu_item = 1
        self._scroll = 0
        self._display.begin()
        self.width = self._display.width
        self.height = self._display.height

# Define image and draw objects for main screen and modal screen
        self._image = Image.new('1', (self.width, self.height))
        self._draw = ImageDraw.Draw(self._image)
        self.clear()

        self._modal_image = Image.new('1', (self.width, self.height))
        self._modal_draw = ImageDraw.Draw(self._modal_image)

        self._clear_image = Image.new('1', (self.width, self.height))
        self._clear_draw = ImageDraw.Draw(self._clear_image)
        self._clear_draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

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
        """ Update the display 4x/sec in separate thread """
        next_update_time = 0
        while True:
            if time()-next_update_time > 0:
                next_update_time = time()+.25
                if (time()-self._modal_timeout) > 0:
                    if self._status == Display.STATUS_STOP:
                        self.display(self._image)
                    else:
                        if self._status == Display.STATUS_PLAY:
                            position = time() - self._main_screen_last_updated + self._seek
                        else:
                            position = self._seek
                        try:
                            duration_label = str(int(self._duration/60)) + ":" + "%02d" % int(self._duration % 60)
                        except TypeError:
                            duration_label = "0:00"
                        try:
                            position_label = str(int(position/60)) + ":" + "%02d" % int(position % 60)
                        except TypeError:
                            position_label = "0:00"
                        scrollable1 = ScrollableText(self._label, self._font)
                        scrollable2 = ScrollableText(position_label + " - " + duration_label, self._font)
                        v_padding = 4
                        v_offset = max(0,
                                int((self.height - scrollable1.textheight - scrollable2.textheight - v_padding)/2))
                        image = scrollable1.draw(self._clear_image, (10,0), self._scroll)
                        image = scrollable2.draw(image, (0, scrollable1.textheight+v_padding), self._scroll)
                        self.display(image)
                        self._scroll = (self._scroll + 10) % 1000000
            sleep(.1)

    def clear(self):
        """ Clear the display """
        self._draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.display(self._image)

    def volume_modal(self, level, delay):
        """ Pop-up window with slider bar for volume """
        textlabel = Display.TXT_VOLUME + ' ' + str(int(level))
        self.display(BarModal(self._image, self._font, textlabel, level).image())
        self._modal_timeout = time() + delay

    def status(self, status_type, delay):
        """ Pop-up window with horizontally and vertically centered text label """
        if status_type == Display.STATUS_PLAY:
            self._status = Display.STATUS_PLAY
            textlabel = Display.TXT_PLAY
        elif status_type == Display.STATUS_PAUSE:
            self._status = Display.STATUS_PAUSE
            textlabel = Display.TXT_PAUSE
        elif status_type == Display.STATUS_STOP:
            self._status = Display.STATUS_STOP
            textlabel = Display.TXT_STOP
        else:
            textlabel = "Huh?"
        self.display(TextModal(self._image, self._font, textlabel).image())
        self._modal_timeout = time() + delay

    def menu(self, delay):
        network = Network()
        if self._menu_item == Display.MENU_NETWORK:
            textlabel = ("ssid: " + network.wpa_supplicant["ssid"], "ip: " + str(network.my_ip()))
        elif self._menu_item == Display.MENU_WIFI:
            textlabel = ("ssid: " + network.hostapd["ssid"], "pw: " + network.hostapd["wpa_passphrase"])
        else:
            textlabel = ("Huh?", "I don't know you")
        self.display(TwoLineTextModal(self._image, self._font, textlabel).image())
        self._modal_timeout = time() + delay
        self._menu_item = self._menu_item + 1
        if self._menu_item > Display.MENU_ITEMS:
            self._menu_item = 1

    def update_main_screen(self, label, duration, seek):
        self._label = label
        self._duration = duration
        self._seek = seek
        self._main_screen_last_updated = time()
# Reset scroll offset when the label changes
        if label != self._prev_label:
            self._scroll = 0
            self._prev_label = label

class Modal(object):
    """ Base class that creates an empty modal """
    def __init__(self, image):

        self._image = image.copy()
        (image_width, image_height) = self._image.size
        self._draw = ImageDraw.Draw(self._image)

        self._x = 4
        y_fraction = 0.2
        self._y = int(y_fraction*image_height)

        self._width = image_width - 2*self._x 
        self._height = image_height - 2*self._y

        self._draw.rectangle((self._x, self._y,\
                self._x+self._width, self._y+self._height), outline=1, fill=0)

    def image(self):
        return self._image

class TextModal(Modal):
    """ Class that creates a modal with a textlabel """

    def __init__(self, image, font, textlabel):

        super(TextModal, self).__init__(image)

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = self._x + max(0, int((self._width-textwidth)/2))
        ytext = self._y + max(0, int((self._height-textheight)/2))
        self._draw.text((xtext, ytext), textlabel, font=font, fill=255)

class TwoLineTextModal(Modal):
    """ Class that creates a modal with a textlabel """

    def __init__(self, image, font, textlabel):

        if not isinstance(textlabel, tuple):
            raise TypeError('textlabel needs to be a tuple')

        super(TwoLineTextModal, self).__init__(image)

        y_padding = 4
        textwidth, textheight = self._draw.textsize(textlabel[0], font=font)
        ytext = self._y + int((self._height - 2*textheight - y_padding)/2)
        for i in (0, 1):
            textwidth, textheight = self._draw.textsize(textlabel[i], font=font)
            xtext = self._x + int((self._width-textwidth)/2)
            self._draw.text((xtext, ytext + i*(textheight + y_padding)), \
                    textlabel[i], font=font, fill=255)

class BarModal(Modal):
    """ Class that creates a modal with a label and a sliderbar"""

    def __init__(self, image, font, textlabel, level):

        super(BarModal, self).__init__(image)

        x_padding = 8
        y_padding = 8
        bar_height = 6

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = self._x + max(0,int((self._width-textwidth)/2))
        ytext = self._y + 4

        self._draw.rectangle((self._x+x_padding, \
                       self._y+self._height-y_padding-bar_height, \
                       self._x+self._width-x_padding, \
                       self._y+self._height-y_padding), outline=1, fill=0)
        self._draw.rectangle((self._x+x_padding, \
                       self._y+self._height-y_padding-bar_height, \
                       self._x+int(self._width*level/100)-x_padding, \
                       self._y+self._height-y_padding), outline=1, fill=1)
        self._draw.text((xtext, ytext), textlabel, font=font, fill=255)

class ScrollableText:
    """ Class to scroll a long textlabel over the screen """
    def __init__(self, textlabel, font):
        self._image = Image.new('1', (10, 10))
        self._draw = ImageDraw.Draw(self._image)
        self.textlabel = textlabel
        self.textwidth, self.textheight = self._draw.textsize(textlabel, font=font)
        self._image = Image.new('1', (self.textwidth+4, self.textheight+4))
        self._draw = ImageDraw.Draw(self._image)
        self._draw.text((0, 0), textlabel, font=font, fill=1)

    def draw(self, image, position, offset):
        """ Draw the label on (x,y) position of an image with starting at <offset> """
        width, height = image.size
        if self.textwidth > width:
            i = offset % (5*int((self.textwidth-width)/5)+40)
        else:
            i = 0
            position = (int((width-self.textwidth)/2),position[1])
        temp=self._image.crop((i,0,width+i,self.textheight))
        image.paste(temp, position)
        return image

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

class Network(object):
    def __init__(self):
        self.hostapd = dict()
        self.wpa_supplicant = dict()
        try:
            file = open("/etc/hostapd/hostapd.conf")
            for line in file:
                try:
                    key ,value = line.split('=')
                    self.hostapd[key] = value[:-1]
                except ValueError:
                    pass
        except IOError:
            pass
        try:
            self.hostapd["ssid"]
        except KeyError:
            self.hostapd["ssid"] = 'unknown'
        try:
            self.hostapd["wpa_passphrase"]
        except KeyError:
            self.hostapd["wpa_passphrase"] = 'unknown'
        try:
            file = open("/etc/wpa_supplicant/wpa_supplicant.conf")
            for line in file:
                try:
                    key ,value = line.split('=')
                    self.wpa_supplicant[key] = value[:-1]
                except ValueError:
                    pass
        except IOError:
            pass
        try:
            self.wpa_supplicant["ssid"]
        except KeyError:
            self.wpa_supplicant["ssid"] = 'unknown'
        try:
            self.wpa_supplicant["psk"]
        except KeyError:
            self.wpa_supplicant["psk"] = 'unknown'

    def my_ip(self):
        return [l for l in \
                ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] \
                if not ip.startswith("127.")][:1], \
                    [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) \
                for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) \
                    if l][0][0]

