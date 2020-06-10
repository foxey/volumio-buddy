# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import os
# Import time functions
from time import time, sleep

# Import thread library for modal timeout handling
from threading import Thread


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

# Imports for INA219 Voltage Sensor Library
from ina219 import INA219, DeviceRangeError

def volumio_buddy_setup():
    """ Setup WiringPi and ensure that it is only executed once """
    global _volumio_buddy_is_setup
    if not '_volumio_buddy_is_setup' in globals():
        _volumio_buddy_is_setup = True
        wiringpi.wiringPiSetup()
    elif not _volumio_buddy_is_setup == True:
        _volumio_buddy_is_setup = True
        wiringpi.wiringPiSetup()

PUD_OFF = wiringpi.GPIO.PUD_OFF
PUD_UP = wiringpi.GPIO.PUD_UP
PUD_DOWN = wiringpi.GPIO.PUD_DOWN

class PushButton:
    """ Class to register a callback function for a pushbutton """

    def __init__(self, gpio_pin, minimum_delay = 0.5, pud = PUD_OFF):
        volumio_buddy_setup()
        self._callback_function = False
        self._callback_args = False
        self.last_push = 0
        self.minimum_delay = minimum_delay
        self.gpio_pin = gpio_pin
        wiringpi.pinMode(gpio_pin, wiringpi.GPIO.INPUT)
        wiringpi.pullUpDnControl(gpio_pin, pud)

    def set_callback(self, callback_function, *callback_args):
        """ Register a function that is called when the knob is turned """
        self._callback_function = callback_function
        self._callback_args = callback_args
        wiringpi.wiringPiISR(self.gpio_pin, wiringpi.INT_EDGE_BOTH, self._callback)

    def _callback(self):
        if time() - self.last_push > self.minimum_delay and self._callback_function:
            self.last_push = time()
            return self._callback_function(*self._callback_args)

class RotaryEncoder:
    """ Class to register callback functions for left and right turns on
        a rotary encoder """

    UNKNOWN = 0
    LEFT = 1
    RIGHT = 2

    def __init__(self, gpio_pin_a, gpio_pin_b, minimum_delay = 0.5, pud = PUD_OFF):
        volumio_buddy_setup()
        self._callback_function = False
        self._callback_args = False
        self.in_critical_section = False
        self.direction = RotaryEncoder.UNKNOWN
        self.prev_direction = RotaryEncoder.UNKNOWN
        self.prev_state = 0
        self.last_push = 0
        self.minimum_delay = minimum_delay
        self.gpio_pin_a = gpio_pin_a
        self.gpio_pin_b = gpio_pin_b
        wiringpi.pinMode(gpio_pin_a, wiringpi.GPIO.INPUT)
        wiringpi.pinMode(gpio_pin_b, wiringpi.GPIO.INPUT)
        wiringpi.pullUpDnControl(gpio_pin_a, pud)
        wiringpi.pullUpDnControl(gpio_pin_b, pud)

    def set_callback(self, callback_function, *callback_args):
        """ Register a function that is called when the knob is turned """
        self._callback_function = callback_function
        self._callback_args = callback_args
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

        if self.in_critical_section == True or not self._callback_function:
            return
        self.in_critical_section = True
        MSB = wiringpi.digitalRead(self.gpio_pin_a)
        LSB = wiringpi.digitalRead(self.gpio_pin_b)
        new_state = (MSB << 1) | LSB
        sum = (self.prev_state << 2) | new_state
        self.prev_state = new_state
        self.in_critical_section = False
        self.prev_direction = self.direction
        if(sum == 0b1101 or sum == 0b0100 or sum == 0b0010 or sum == 0b1011):
            self.direction = RotaryEncoder.LEFT
        elif (sum == 0b1110 or sum == 0b0111 or sum == 0b0001 or sum == 0b1000):
            self.direction = RotaryEncoder.RIGHT
        else:
            self.direction = RotaryEncoder.UNKNOWN
        if time() - self.last_push > self.minimum_delay and self._callback_function:
            self.last_push = time()
            return self._callback_function(*self._callback_args)

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

# Default show duration for modal windows (sec)
    MODAL_DURATION = 3

# Menu reset timeout
    MENU_TIMEOUT = 3 * MODAL_DURATION

# Text modal type definitions
    STATUS_PLAY = 1
    STATUS_PAUSE = 2
    STATUS_STOP = 3
# Text label definitions
    TXT_VOLUME = "Volume"
    TXT_PLAY = "Play"
    TXT_PAUSE = "Pause"
    TXT_STOP = "Stop"

    def __init__(self, reset_pin):
        self.reset_pin = reset_pin
        self._display =  Adafruit_SSD1306.SSD1306_128_64(rst=reset_pin)
        self._status = Display.STATUS_STOP
        self._prev_status = Display.STATUS_STOP
        self._label = ""
        self._prev_label = ""
        self._duration = 0
        self._seek = 0
        self._main_screen_last_updated = 0
        self._modal = False
        self._modal_timeout = 0
        self._modal_duration = Display.MODAL_DURATION
        self._menu_item = 0
        self._menu_items = None
        self._menu_timeout = Display.MENU_TIMEOUT
        self._display.begin()
        self.width = self._display.width
        self.height = self._display.height
        self._scroll = -self.width
        self.update_interval = 0.1

# Define image and draw objects for main screen and modal screen
        self._image = Image.new('1', (self.width, self.height))
        self._draw = ImageDraw.Draw(self._image)
        self.clear()

        self._logo_image = Image.new('1', (self.width, self.height))

# Load font. If TTF file is not found, load default font
# Make sure the .ttf font file is in the same directory as
# the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
        try:
            self._font = ImageFont.truetype(os.path.dirname(os.path.realpath(__file__)) + '/pixChicago.ttf', 12)
        except IOError:
            self._font = ImageFont.load_default()
        try:
            self._modal_font = ImageFont.truetype(os.path.dirname(os.path.realpath(__file__)) + '/Vera.ttf', 12)
        except:
            self._modal_font = ImageFont.load_default()

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
            self._logo_image = Image.open(filename). \
                resize((self.width, self.height), Image.ANTIALIAS).convert('1')
            self._image.paste(self._logo_image)
            self.display(self._image)
        except IOError:
            print "Cannot open file %s" % filename
            pass 

    def _update(self):
        """ Update the display 4x/sec in separate thread """
        next_update_time = 0
        while self.update_interval > 0:
            if time()-next_update_time > 0:
                next_update_time = time()+1.5*self.update_interval
                if self._status == Display.STATUS_STOP:
                    self._image.paste(self._logo_image)
                else:
                    self.draw_main_screen()
                if (time()-self._modal_timeout) < 0 and self._modal:
                    self._image.paste(self._modal.image(), (self._modal.x, self._modal.y))
                self.display(self._image)
            sleep(self.update_interval)

# Start thread that will update the screen regulary
    def start_updates(self, interval = 0.1):
        self.update_interval = interval
        update_thread = Thread(target=self._update, args=())
        update_thread.start()
        print "started display update thread"

    def clear(self):
        """ Clear the display """
        self._draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.display(self._image)

    def volume(self, level):
        """ Pop-up window with slider bar for volume """
        textlabel = Display.TXT_VOLUME + ' ' + str(int(level))
        self._modal_timeout = time() + self._modal_duration
        self._modal = BarModal(self._image, self._font, textlabel, level)

    def status(self, status_type):
        """ Pop-up window with horizontally and vertically centered text label """
        if status_type not in [Display.STATUS_PLAY, Display.STATUS_PAUSE, Display.STATUS_STOP] \
            or status_type == self._status:
            return
        self._prev_status = self._status
        self._status = status_type
        if status_type == Display.STATUS_PLAY and self._prev_status == Display.STATUS_PAUSE:
            self._modal_timeout = time() + self._modal_duration
            self._modal = TextModal(self._image, self._font, Display.TXT_PLAY)
        elif status_type == Display.STATUS_PAUSE and self._prev_status == Display.STATUS_PLAY:
            self._modal_timeout = time() + self._modal_duration
            self._modal = TextModal(self._image, self._font, Display.TXT_PAUSE)

    def set_modal_duration(self, duration):
        self._modal_duration = duration

    def set_menu_items(self, *items):
        self._menu_items = items[0]

    def menu(self):
        """ Cycle through the menu modals """
        if self._modal_timeout + self._menu_timeout < time():
            self._menu_item = 0
        textlabel = self._menu_items[self._menu_item].textlabel()
        self._modal_timeout = time() + self._modal_duration
        self._modal = TwoLineTextModal(self._image, self._modal_font, textlabel)
        self._menu_item = self._menu_item + 1
        self._menu_item = (self._menu_item + 1) % len(self._menu_items)

    def draw_main_screen(self):
        v_offset = 2
        v_padding = 4
        bar_height = 4
        separator_label = ' - '
        if self._status == Display.STATUS_PLAY:
            position = time() - self._main_screen_last_updated + self._seek
        else:
            position = 1.0 * self._seek
        try:
            remaining = max(self._duration - position, 0)
            duration_label = str(int(remaining/60)) + ":" + \
                                "%02d" % int(remaining % 60)
        except TypeError:
            duration_label = "-:--"
        try:
            position_label = str(int(position/60)) + ":" + "%02d" % int(position % 60)
# The position_minutes string is used to determine the width of the label to ensure the colon
# is always at the same position
            position_minutes = str(int(position/60)) + ":00"
        except TypeError:
            position_label = "0:00"
        try:
            rel_position = min(100, max(0, position/self._duration))
        except (NameError, TypeError, ZeroDivisionError):
            rel_position = 0
            bar_height = 0
        self._draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        separator_label_width, separator_label_height = self._draw.textsize(separator_label, font=self._font)
        position_label_width, position_label_height = self._draw.textsize(position_minutes, font=self._font)
        scrollable = ScrollableText(self._label, self._font)
# Draw the artist, album and song title (scrolling)
        scrollable.draw(self._image, (0,v_offset), self._scroll)
# Draw the current position in the song
        self._draw.text(((self.width - separator_label_width)/2 - position_label_width, \
                v_offset + scrollable.textheight + v_padding), \
                position_label, font=self._font, fill=1)
# Draw the total duration of the song + the separator. Ensure that the separator is centered horizontally
        self._draw.text(((self.width - separator_label_width)/2, \
                v_offset + scrollable.textheight + v_padding), \
                separator_label+duration_label, font=self._font, fill=1)
# Draw the progress bar only when height > 0
        if bar_height > 0:
            self._draw.rectangle((0, self.height - 1 - bar_height, \
                           self.width - 1, self.height - 1), outline=1, fill=0)
            self._draw.rectangle((0, self.height - 1 - bar_height, \
                           int((self.width - 1)*rel_position), self.height - 1), outline=1, fill=1)
# Increment the scroll 'cursor'
        self._scroll = self._scroll + 10
        if self._scroll > scrollable.textwidth:
           self._scroll = -self.width

    def update_main_screen(self, label, duration, seek):
        """ Update the text label, the seek time and the duration on the current song """
        self._label = label
        self._duration = duration
        self._seek = seek
        self._main_screen_last_updated = time()
# Reset scroll offset when the label changes
        if label != self._prev_label:
            self._scroll = -self.width
            self._prev_label = label

class Modal(object):
    """ Base class that creates an empty modal """
    def __init__(self, image):

        self.x = 4
        y_fraction = 0.2
        (image_width, image_height) = image.size
        self.y = int(y_fraction*image_height)
        self.width = image_width - 2*self.x 
        self.height = image_height - 2*self.y

        self._image = Image.new('1', (self.width, self.height))
        self._draw = ImageDraw.Draw(self._image)

        self._draw.rectangle((0, 0, self.width - 1, self.height - 1), outline=1, fill=0)

    def image(self):
        return self._image

class TextModal(Modal):
    """ Class that creates a modal with a textlabel """

    def __init__(self, image, font, textlabel):

        super(TextModal, self).__init__(image)

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = max(0, int((self.width-textwidth)/2))
        ytext = max(0, int((self.height-textheight)/2))
        self._draw.text((xtext, ytext), textlabel, font=font, fill=255)

class TwoLineTextModal(Modal):
    """ Class that creates a modal with a textlabel """

    def __init__(self, image, font, textlabel):

        if not isinstance(textlabel, tuple):
            raise TypeError('textlabel needs to be a tuple')

        super(TwoLineTextModal, self).__init__(image)

        y_padding = 2
        textwidth, textheight = self._draw.textsize(textlabel[0], font=font)
        ytext = int((self.height - 2*textheight - y_padding)/2)
        for i in (0, 1):
            textwidth, textheight = self._draw.textsize(textlabel[i], font=font)
            xtext = int((self.width-textwidth)/2)
            self._draw.text((xtext, ytext + i*(textheight + y_padding)), \
                    textlabel[i], font=font, fill=255)

class BarModal(Modal):
    """ Class that creates a modal with a label and a sliderbar"""

    def __init__(self, image, font, textlabel, level):

        super(BarModal, self).__init__(image)

        x_padding = 8
        y_padding = 8
        bar_height = 4

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = max(0,int((self.width-textwidth)/2))
        ytext = 4

        self._draw.rectangle((x_padding, \
                       self.height - y_padding - bar_height, \
                       self.width - x_padding, \
                       self.height - y_padding), outline=1, fill=0)
        self._draw.rectangle((x_padding, \
                       self.height - y_padding-bar_height, \
                       x_padding + int((self.width - 2*x_padding)*level/100), \
                       self.height - y_padding), outline=1, fill=1)
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
        i = 0
        if self.textwidth <= width:
            position = (int((width-self.textwidth)/2),position[1])
        elif offset < 0:
            position = (-offset, position[1])
        else:
            i = offset % (self.textwidth+int(0.1*width))
        temp=self._image.crop((i,0,width+i,self.textheight))
        wiringpi.piLock(0)
        image.paste(temp, position)
        wiringpi.piUnlock(0)

class VolumioClient:
    """ Class for the websocket client to Volumio """

    def __init__(self):
        HOSTNAME='localhost'
        PORT=3000

        self._callback_function = False
        self._callback_args = False
        self.state = dict()
        self.state["status"] = ""
        self.prev_state = dict()
        self.prev_state["status"] = ""
        self.last_update_time = 0

        def _on_pushState(*args):
            self.state = args[0]
            if self._callback_function:
                self._callback_function(*self._callback_args)
            self.prev_state = self.state

        self._client = SocketIO(HOSTNAME, PORT, LoggingNamespace)
        self._client.on('pushState', _on_pushState)
        self._client.emit('getState', _on_pushState)
        self._client.wait_for_callbacks(seconds=1)

    def set_callback(self, callback_function, *callback_args):
        self._callback_function = callback_function
        self._callback_args = callback_args

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

    def previous(self):
        self._client.emit('prev')

    def next(self):
        self._client.emit('next')

    def seek(self, seconds):
        self._client.emit('seek', int(seconds))

    def wait(self, **kwargs):
        self.wait_thread = Thread(target=self._wait, args=(kwargs))
        self.wait_thread.start()
        print "started websocket wait thread"
        return self.wait_thread

    def _wait(self, **kwargs):
        while True:
            self._client.wait(kwargs)
            print "websocket wait loop terminated, restarting"

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
        try:
            return [l for l in \
                    ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] \
                    if not ip.startswith("127.")][:1], \
                        [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) \
                    for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) \
                        if l][0][0]
        except:
            return None

class PipeWriter(object):
    IN=0
    OUT=1
    def __init__(self):
        self.pipein, self.pipeout = os.pipe()

    def write(self, command):
        os.write(self.pipeout, '%s\n' % command)

    def read(self):
        return self.pipein.readline()[:-1]

    def close(self, direction):
        if direction == PipeWriter.IN:
            os.close(self.pipein)
        elif direction == PipeWriter.OUT:
            os.close(self.pipeout)
            self.pipein = os.fdopen(self.pipein)

class Battery(object):
    SHUNT_OHMS = 0.1
    CELL_COUNT = 5
    FULL = 4.2 # Maximum voltage of a 18650 LiPo Cell
    LOW = 2.9
    WARN = 3.2
    EMPTY = 2.8
    def __init__(self):
        self._ina = INA219(Battery.SHUNT_OHMS)
        self._ina.configure()
        self.cell_count = Battery.CELL_COUNT
        self.full = Battery.FULL
        self.low = Battery.LOW
        self.warn = Battery.WARN
        self.empty = Battery.EMPTY
        self._warn_function = None
        self._warn_function_args = None
        self._empty_function = None
        self._empty_function_args = None

    def voltage(self):
        return self._ina.voltage()

    def level(self):
        return int(100*(self.voltage()/self.cell_count-self.low)/(self.full-self.low))

    def set_warn_function(self, function, *args):
        self._warn_function = function
        self._warn_function_args = args

    def set_empty_function(self, function, *args):
        self._empty_function = function
        self._empty_function_args = args

    def start_monitor(self, *kwargs):
        wait_thread = Thread(target=self._monitor, args=(kwargs))
        wait_thread.start()
        print "started battery polling thread"
        return wait_thread

    def _monitor(self, polling_interval=10):
        while True:
            voltage=self.voltage()
            if voltage <= self.cell_count*self.warn and self._warn_function:
                print "Battery._monitor: call _warn_function (v=%.3f)" % voltage
                self._warn_function(*self._warn_function_args)
            if voltage <= self.cell_count*self.EMPTY and self._empty_function:
                print "Battery._monitor: call _empty_function (v=%.3f)" % voltage
                self._empty_function(*self._empty_function_args)
            sleep(polling_interval)
