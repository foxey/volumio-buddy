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

import logging
import RPi.GPIO as GPIO
from time import time


PUD_UP = GPIO.PUD_UP
PUD_DOWN = GPIO.PUD_DOWN
PUD_OFF = GPIO.PUD_OFF


def cleanup():
    GPIO.cleanup()


class PushButton:
    """ Pushbutton with configurable callback function"""

    def __init__(self, gpio_pin, minimum_delay=0.5, pull=PUD_OFF):
        self._callback_function = False
        self._callback_args = False
        self.last_push = 0
        self.minimum_delay = minimum_delay
        self.gpio_pin = gpio_pin
        # mode must be set to GPIO.BCM, since CircuitPython
        # (used for the SSD1306 OLED display) uses that under the hood
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=pull)

    def set_callback(self, callback_function, *callback_args):
        """ Register a function that is called when the button is pushed """
        if not callable(callback_function):
            raise TypeError('Argument for handler function is not a function, but a {}.'
                            .format(type(callback_function)))
        self._callback_function = callback_function
        self._callback_args = callback_args
        GPIO.add_event_detect(self.gpio_pin, GPIO.BOTH)
        GPIO.add_event_callback(self.gpio_pin, self._callback)
        logging.info('Callback {} registered for PushButton'
                     .format(callback_function.__name__))

    def _callback(self, channel):
        if time() - self.last_push > self.minimum_delay and self._callback_function:
            self.last_push = time()
            logging.debug('Executing callback for PushButton')
            return self._callback_function(*self._callback_args)

    def off(self):
        GPIO.remove_event_detect(self.gpio_pin)
        self._callback_function = None


class RotaryEncoder:
    """ Class to register callback functions for left and right turns on
        a rotary encoder """

    UNKNOWN = 0
    LEFT = 1
    RIGHT = 2

    def __init__(self, gpio_pin_a, gpio_pin_b, minimum_delay=0.1, pull=GPIO.PUD_UP):
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
        # mode must be set to GPIO.BCM, since CircuitPython
        # (used for the SSD1306 OLED display) uses that under the hood
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpio_pin_a, GPIO.IN, pull_up_down=pull)
        GPIO.setup(gpio_pin_b, GPIO.IN, pull_up_down=pull)

    def set_callback(self, callback_function, *callback_args):
        """ Register a function that is called when the knob is turned """
        if not callable(callback_function):
            raise TypeError('Argument for handler function is not a function, but a {}.'
                            .format(type(callback_function)))
        self._callback_function = callback_function
        self._callback_args = callback_args
        GPIO.add_event_detect(self.gpio_pin_a, GPIO.BOTH, bouncetime=10)
        GPIO.add_event_callback(self.gpio_pin_a, self._decode_rotary)
        GPIO.add_event_detect(self.gpio_pin_b, GPIO.BOTH, bouncetime=10)
        GPIO.add_event_callback(self.gpio_pin_b, self._decode_rotary)
        logging.info('Callback {} registered for RotaryEncoder'
                     .format(callback_function.__name__))

    def _decode_rotary(self, channel):
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

        if self.in_critical_section is True or not self._callback_function:
            logging.debug('In critical section')
            return
        self.in_critical_section = True
        MSB = GPIO.input(self.gpio_pin_a)
        LSB = GPIO.input(self.gpio_pin_b)
        new_state = (MSB << 1) | LSB
        sum = (self.prev_state << 2) | new_state
        self.prev_state = new_state
        self.in_critical_section = False
        self.prev_direction = self.direction
        if(sum == 0b1101 or sum == 0b0100 or sum == 0b0010 or sum == 0b1011):
            logging.info('Rotary encoder state: {0:04b} (LEFT)'.format(int(sum)))
            self.direction = RotaryEncoder.LEFT
        elif (sum == 0b1110 or sum == 0b0111 or sum == 0b0001 or sum == 0b1000):
            logging.info('Rotary encoder state: {0:04b} (RIGHT)'.format(int(sum)))
            self.direction = RotaryEncoder.RIGHT
        else:
            logging.info('Rotary encoder state: {0:04b} (UNKNOWN)'.format(int(sum)))
            self.direction = RotaryEncoder.UNKNOWN
            return None
        if time() - self.last_push > self.minimum_delay and self._callback_function:
            self.last_push = time()
            return self._callback_function(*self._callback_args)
        else:
            logging.info('Debounce active.')
            return None

    def off(self):
        GPIO.remove_event_detect(self.gpio_pin_a)
        GPIO.remove_event_detect(self.gpio_pin_b)
        self._callback_function = None


class RGBValueOutOfRange(Exception):
    def __init__(self, message='Value should be between 0-100.'):
        self.message = message
        super().__init__(self, message)


class RGBLED():
    """ RGB LED driver using software based PWM """

    PWM_FREQ = 100
    DIM_RED = (10, 0, 0)
    DIM_GREEN = (0, 10, 0)
    DIM_BLUE = (0, 0, 10)
    BRIGHT_RED = (25, 0, 0)
    BRIGHT_GREEN = (0, 25, 0)
    BRIGHT_BLUE = (0, 0, 25)

    def __init__(self, gpio_pin_r, gpio_pin_g, gpio_pin_b):
        self.gpio_pin_r = gpio_pin_r
        self.gpio_pin_g = gpio_pin_g
        self.gpio_pin_b = gpio_pin_b
        self.values = (0, 0, 0)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpio_pin_r, GPIO.OUT)
        GPIO.setup(gpio_pin_g, GPIO.OUT)
        GPIO.setup(gpio_pin_b, GPIO.OUT)
        self.pwm = [GPIO.PWM(gpio_pin_r, RGBLED.PWM_FREQ),
                    GPIO.PWM(gpio_pin_g, RGBLED.PWM_FREQ),
                    GPIO.PWM(gpio_pin_b, RGBLED.PWM_FREQ)]

    def set(self, values):
        """ Set the values of each color to 0-100 """
        for value in values:
            if value not in range(0, 101):
                raise RGBValueOutOfRange
        self.values = values
        for i in range(0, 3):
            self.pwm[i].start(values[i])

    def off(self):
        for i in range(0, 3):
            self.pwm[i].stop()
