# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import wiringpi

def volumio_buddy_setup():
    global _volumio_buddy_is_setup
    if not 'volumio_buddy_is_setup' in vars():
        volumio_buddy_is_setup = True
        wiringpi.wiringPiSetup()
    elif not volumio_buddy_is_setup == True:
        volumio_buddy_is_setup = True
        wiringpi.wiringPiSetup()

class RotaryEncoder:
    """ Class to register callback functions for left and right turns on
        a rotary encoder """
    LEFT = 0
    RIGHT = 1
    def __init__(self, gpio_pin_a, gpio_pin_b):
        volumio_buddy_setup()
        self.in_critical_section = False
        self.prev_state = 0
        self.gpio_pin_a = gpio_pin_a
        self.gpio_pin_b = gpio_pin_b
        wiringpi.pinMode(gpio_pin_a, 0)
        wiringpi.pinMode(gpio_pin_b, 0)

    def set_callback(self, callback_function):
        self.callback_function = callback_function
        wiringpi.wiringPiISR(self.gpio_pin_a, wiringpi.INT_EDGE_BOTH, self._decode_rotary)
        wiringpi.wiringPiISR(self.gpio_pin_b, wiringpi.INT_EDGE_BOTH, self._decode_rotary)

    def _decode_rotary(self):
        if self.in_critical_section == True:
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

