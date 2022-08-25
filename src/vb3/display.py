# Copyright (c) 2022 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
#
# This file is part of Volumio-buddy.
#
# Volumio-buddy is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# Volumio-buddy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Volumio-buddy. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
import os
from PIL import Image, ImageFont, ImageDraw
import re
from time import time
# Import needed board pins.
from board import SCL, SDA
import busio

# Import the SSD1306 module.
import adafruit_ssd1306


class Display:
    """ Class for the user interface using a 128x64 OLED SSD1306 compatible display """
# Display dimensions
    WIDTH = 128
    HEIGHT = 64
# Default show duration for modal windows (sec)
    MODAL_DURATION = 3

# Popup reset timeout
    POPUP_TIMEOUT = 3 * MODAL_DURATION

# Text modal type definitions
    VOLUME = 0
    STATUS_CONNECTING = 1
    STATUS_RECONNECTING = 2
    STATUS_PLAY = 3
    STATUS_PAUSE = 4
    STATUS_STOP = 5
    STATUS_SHUTDOWN = 6

# Text label definitions
    LABEL = {VOLUME: 'Volume',
             STATUS_CONNECTING: 'Connecting',
             STATUS_RECONNECTING: 'Reconnecting',
             STATUS_PLAY: 'Play',
             STATUS_PAUSE: 'Pause',
             STATUS_STOP: 'Stop',
             STATUS_SHUTDOWN: 'Shutdown'}

    def __init__(self, i2c_addr=None):
        self._status = Display.STATUS_STOP
        self._prev_status = Display.STATUS_STOP
        self._label = ''
        self._prev_label = ''
        self._duration = 0
        self._seek = 0
        self._main_screen_last_updated = 0
        self._modal = False
        self._modal_timeout = 0
        self._modal_duration = Display.MODAL_DURATION
        self._current_popup = 0
        self._popup = []
        self._popup_timeout = Display.POPUP_TIMEOUT
        i2c = busio.I2C(SCL, SDA)
        self._display = adafruit_ssd1306.SSD1306_I2C(self.WIDTH, self.HEIGHT, i2c, addr=i2c_addr or 0x3c)
        self.width = self._display.width
        self.height = self._display.height
        self._scroll = -self.width
        self.update_interval = 0.1

# Define image and draw objects for main screen and modal screen
        self._image = Image.new('1', (self.width, self.height))
        self._draw = ImageDraw.Draw(self._image)
        self.clear()
        self.logo_image()

# Load font. If TTF file is not found, load default font
# Make sure the .ttf font file is in the same directory as
# the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
        try:
            self._font = ImageFont.truetype(os.path.dirname(os.path.realpath(__file__)) + '/pixChicago.ttf', 12)
        except IOError:
            self._font = ImageFont.load_default()
        try:
            self._popup_font = ImageFont.truetype(os.path.dirname(os.path.realpath(__file__)) + '/Vera.ttf', 11)
        except IOError:
            self._popup_font = ImageFont.load_default()

    def show(self, image):
        """ Update display with new image """
        self._display.image(image)
        self._display.show()

    def logo_image(self, filename=None):
        """ Show a logo """
        if not filename:
            filename = os.path.dirname(os.path.realpath(__file__)) + '/volumio.ppm'
        try:
            self._logo_image = Image.open(filename). \
                resize((self.width, self.height), Image.ANTIALIAS).convert('1')
            self._image.paste(self._logo_image)
            self.show(self._image)
        except IOError:
            logging.error('Cannot open file %s' % filename)
            pass

    def update(self):
        if self._status == Display.STATUS_PLAY or self._status == Display.STATUS_PAUSE:
            self.draw_main_screen()
        else:
            self._image.paste(self._logo_image)
        if (time()-self._modal_timeout) < 0 and self._modal:
            self._image.paste(self._modal.image(), (self._modal.x, self._modal.y))
        self.show(self._image)

# Asyncio task to update the screen regulary
    async def updater(self, interval=0.1):
        """ Update the display 4x/sec in separate task """
        self.update_interval = interval
        next_update_time = 0
        logging.info('started display update task')
        while self.update_interval > 0:
            if time()-next_update_time > 0:
                next_update_time = time()+1.5*self.update_interval
                self.update()
            await asyncio.sleep(self.update_interval)

    def clear(self):
        """ Clear the display """
        self._draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.show(self._image)

    def volume(self, level):
        """ Pop-up window with slider bar for volume """
        textlabel = Display.LABEL[Display.VOLUME] + ' ' + str(int(level))
        self._modal_timeout = time() + self._modal_duration
        self._modal = BarModal(self._image, self._font, textlabel, level)

    def status(self, status_type):
        """ Pop-up window with horizontally and vertically centered text label """
        if status_type not in Display.LABEL.keys() or status_type == self._status:
            return
        logging.debug('Set status to {}'.format(status_type))
        self._prev_status = self._status
        self._status = status_type
        if status_type != Display.STATUS_STOP and status_type != self._prev_status:
            self._modal_timeout = time() + self._modal_duration
            self._modal = TextModal(self._image, self._font, Display.LABEL[status_type])

    def set_modal_duration(self, duration):
        self._modal_duration = duration

    def add_popup(self, popup):
        self._popup.append(popup)

    def show_next_popup(self):
        """ Cycle through the popup modals """
        if self._modal_timeout + self._popup_timeout < time():
            self._current_popup = 0
        logging.info('Showing popup {} from {}.'.format(self._current_popup + 1, len(self._popup)))
        label = self._popup[self._current_popup].label()
        self._modal_timeout = time() + self._modal_duration
        if type(label) is tuple:
            self._modal = TwoLineTextModal(self._image, self._popup_font, label)
        elif type(label) is str:
            self._modal = TextModal(self._image, self._popup_font, label)
        else:
            raise TypeError('Textlabel is a {}. Should be string or tuple'
                            .format(type(label).__name__))
        self._current_popup = (self._current_popup + 1) % len(self._popup)

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
            duration_label = str(int(remaining/60)) + ':' + \
                '%02d' % int(remaining % 60)
        except TypeError:
            duration_label = '-:--'
        try:
            position_label = str(int(position/60)) + ':' + '%02d' % int(position % 60)
# The position_minutes string is used to determine the width of the label to ensure the colon
# is always at the same position
            position_minutes = str(int(position/60)) + ':00'
        except TypeError:
            position_label = '0:00'
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
        scrollable.draw(self._image, (0, v_offset), self._scroll)
# Draw the current position in the song
        self._draw.text(((self.width - separator_label_width)/2 - position_label_width,
                         v_offset + scrollable.textheight + v_padding),
                        position_label, font=self._font, fill=1)
# Draw the total duration of the song + the separator. Ensure that the separator is centered horizontally
        self._draw.text(((self.width - separator_label_width)/2,
                         v_offset + scrollable.textheight + v_padding),
                        separator_label+duration_label, font=self._font, fill=1)
# Draw the progress bar only when height > 0
        if bar_height > 0:
            self._draw.rectangle((0, self.height - 1 - bar_height,
                                  self.width - 1, self.height - 1), outline=1, fill=0)
            self._draw.rectangle((0, self.height - 1 - bar_height,
                                  int((self.width - 1)*rel_position), self.height - 1),
                                 outline=1, fill=1)
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
            self._draw.text((xtext, ytext + i*(textheight + y_padding)),
                            textlabel[i], font=font, fill=255)


class BarModal(Modal):
    """ Class that creates a modal with a label and a sliderbar"""

    def __init__(self, image, font, textlabel, level):

        super(BarModal, self).__init__(image)

        if type(level) is not int or level < 0 or level > 100:
            raise ValueError

        x_padding = 8
        y_padding = 8
        bar_height = 4

        textwidth, textheight = self._draw.textsize(textlabel, font=font)
        xtext = max(0, int((self.width-textwidth)/2))
        ytext = 4

        self._draw.rectangle((x_padding,
                              self.height - y_padding - bar_height,
                              self.width - x_padding,
                              self.height - y_padding), outline=1, fill=0)
        self._draw.rectangle((x_padding,
                              self.height - y_padding - bar_height,
                              x_padding + int((self.width - 2*x_padding)*level/100),
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
            position = (int((width-self.textwidth)/2), position[1])
        elif offset < 0:
            position = (-offset, position[1])
        else:
            i = offset % (self.textwidth+int(0.1*width))
        temp = self._image.crop((i, 0, width+i, self.textheight))
        image.paste(temp, position)


class InvalidLabelError(Exception):
    def __init__(self, labeltext, message='Invalid label for Popup: {}'):
        self.labeltext = labeltext
        self.message = message
        super().__init__(self, message)

    def __str__(self):
        return self.message.format(self.labeltext)


class LabelArgsMismatchException(Exception):
    def __init__(self, placeholders, n_args, message='Label format for {} args, but {} given'):
        self.placeholders = placeholders
        self.n_args = n_args
        self.message = message
        super().__init__(self, message)

    def __str__(self):
        return self.message.format(self.placeholders, self.n_args)


class Popup:
    def __init__(self, labeltext, *args):
        Popup.validate_label(labeltext)
        Popup.validate_placeholders(labeltext, args)
        Popup.validate_args(args)
        self._args = args
        self._labeltext = labeltext

    def label(self):
        result = []
        for arg in self._args:
            if type(arg) is str:
                result.append(arg)
            else:
                result.append(arg())
        if type(self._labeltext) is str:
            return self._labeltext.format(*result)
        else:
            offset = len(re.findall('{.*?}', self._labeltext[0]))
            return (self._labeltext[0].format(*result),
                    self._labeltext[1].format(*result[offset:]))

    @staticmethod
    def validate_label(labeltext):
        if type(labeltext) is tuple:
            if len(labeltext) != 2 or \
                    type(labeltext[0]) is not str or type(labeltext[1]) is not str:
                raise InvalidLabelError(labeltext)
        else:
            if type(labeltext) is not str:
                raise InvalidLabelError(labeltext)

    @staticmethod
    def validate_placeholders(labeltext, args):
        placeholders = len(re.findall('{.*?}', ''.join(labeltext)))
        if placeholders != len(args):
            raise LabelArgsMismatchException(placeholders, len(args))

    @staticmethod
    def validate_args(args):
        for i in range(len(args)):
            if not callable(args[i]) and type(args[i]) is not str:
                raise TypeError('Argument {} for popup is not a function or string, but a {}.'
                                .format(i, type(args[i]).__name__))
