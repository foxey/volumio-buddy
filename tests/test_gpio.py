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

import unittest.mock as mock
import pytest
from .context import vb3


pin = 7
pin_a = 16
pin_b = 18
led_pin_r = 13
led_pin_g = 12
led_pin_b = 6
pull = vb3.gpio.PUD_UP
pushbutton = vb3.PushButton(pin, pull=pull)
rotary_encoder = vb3.RotaryEncoder(pin_a, pin_b, pull=pull)
callback_arg = [1]


def callback(arg):
    pass


@mock.patch('RPi.GPIO.setup')
def test_pushbutton(patched_setup):
    assert pushbutton.gpio_pin == pin
    assert patched_setup.called_once_with(pin, pull)


def test_pushbutton_callback():
    assert pushbutton.set_callback(callback, callback_arg) is None
    with pytest.raises(TypeError):
        pushbutton.set_callback(pushbutton, callback_arg)


@mock.patch('RPi.GPIO.setup')
def test_rotary_encoder(patched_setup):
    assert rotary_encoder.gpio_pin_a == pin_a
    assert rotary_encoder.gpio_pin_b == pin_b
    assert patched_setup.called_once_with(pin_a, pull)
    assert patched_setup.called_once_with(pin_b, pull)


def test_rotary_encoder_callback():
    assert rotary_encoder.set_callback(callback, callback_arg) is None
    with pytest.raises(TypeError):
        rotary_encoder.set_callback(rotary_encoder, callback_arg)


def test_rotary_encoder_decode():
    assert rotary_encoder._decode_rotary(pin_a) is None


@mock.patch('RPi.GPIO.setup')
@mock.patch('RPi.GPIO.PWM')
def test_led(patched_pwm, patched_setup):
    led = vb3.RGBLED(led_pin_r, led_pin_g, led_pin_b)
    led.set(vb3.RGBLED.DIM_RED)
    assert led.values == vb3.RGBLED.DIM_RED
    patched_pwm.assert_called()


@mock.patch('RPi.GPIO.cleanup')
def test_clean_up(patched_cleanup):
    vb3.gpio.cleanup()
    assert patched_cleanup.called_once()
