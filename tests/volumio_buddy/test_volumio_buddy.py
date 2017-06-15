# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import unittest
try:
    import mock
    from mock import call, patch
except ImportError:
    from unittest import mock
    from unittest.mock import call, patch
import wiringpi

from os import path
from time import sleep
from volumio_buddy import volumio_buddy_setup, PushButton, RotaryEncoder, RGBLED, Display
from volumio_buddy import __file__ as filename

@patch('wiringpi.wiringPiSetup', autospec=True)
@patch('wiringpi.pinMode', autospec=True)
@patch('wiringpi.wiringPiISR', autospec=True)

class TestVolumioBuddy(unittest.TestCase):
        
    def test0_volumio_buddy_setup(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        volumio_buddy_setup()
        mock_wiringpi_setup.assert_called_once_with()
        volumio_buddy_setup()
        mock_wiringpi_setup.assert_called_once_with()
        volumio_buddy_setup()
        mock_wiringpi_setup.assert_called_once_with()

    def test1_PushButton_set_callback(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        d = dict()
        d[0] = 1
        def callback_function(arg):
            return 1
        gpio_pin = 1
        p = PushButton(gpio_pin)
        mock_wiringpi_pinMode.assert_called_with(gpio_pin, 0)
        p.set_callback(callback_function, d)
        mock_wiringpi_ISR.assert_called_with(gpio_pin, wiringpi.INT_EDGE_BOTH, p._callback)

    def test2_PushButton__callback(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        d = dict()
        d[0] = 1
        def callback_function(arg):
            return arg[0] 
        gpio_pin = 1
        p = PushButton(gpio_pin)
        mock_wiringpi_pinMode.assert_called_with(gpio_pin, 0)
        p.set_callback(callback_function, d)
        self.assertEqual(p._callback(), 1)

    def test3_PushButton__callback(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        d = dict()
        d[0] = 1
        def callback_function(arg):
            return arg[0] 
        gpio_pin = 1
        p = PushButton(gpio_pin)
        mock_wiringpi_pinMode.assert_called_with(gpio_pin, 0)
        p.set_callback(callback_function, d)
        d[0] = 2
        self.assertEqual(p._callback(), 2)

    def test4_RotaryEncoder_set_callback(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        d = dict()
        d[0] = 1
        def callback_function(arg):
            return 1
        gpio_pin_a = 1
        gpio_pin_b = 1
        r = RotaryEncoder(gpio_pin_a, gpio_pin_b)
        r.set_callback(callback_function, r, d)
        mock_wiringpi_ISR.assert_called_with(gpio_pin_b, wiringpi.INT_EDGE_BOTH, r._decode_rotary)

    @patch('wiringpi.digitalRead', side_effect=[0, 1, 1, 1, 0 , 1, 0, 0])
    def test5_RotaryEncoder_set_callback(self, mock_wiringpi_digital_read, mock_wiringpi_ISR, \
            mock_wiringpi_pinMode, mock_wiringpi_setup):
        d = dict()
        def callback_function(r, arg):
            return r.direction, d[0]
        gpio_pin_a = 1
        gpio_pin_b = 1
        r = RotaryEncoder(gpio_pin_a, gpio_pin_b)
        r.set_callback(callback_function, r, d)
        d[0] = 1
        self.assertEqual(r._decode_rotary(), (RotaryEncoder.RIGHT, 1))
        sleep(1)
        self.assertEqual(r._decode_rotary(), (RotaryEncoder.RIGHT, 1))
        d[0] = 2
        sleep(1)
        self.assertEqual(r._decode_rotary(), (RotaryEncoder.LEFT, 2))
        sleep(1)
        self.assertEqual(r._decode_rotary(), (RotaryEncoder.LEFT, 2))

    @patch('wiringpi.softPwmWrite', autospec = True)
    @patch('wiringpi.softPwmCreate', autospec = True)
    def test6_RGBLED_set(self, mock_wiringpi_softPwmCreate, mock_wiringpi_softPwmWrite, \
            mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        gpio_pin_r = 10
        gpio_pin_g = 8
        gpio_pin_b = 6
        led = RGBLED(gpio_pin_r, gpio_pin_g, gpio_pin_b)
        calls = [call(gpio_pin_r, 1), call(gpio_pin_g, 1), call(gpio_pin_b, 1)]
        mock_wiringpi_pinMode.assert_has_calls(calls)
        calls = [call(gpio_pin_r, 0, 100), call(gpio_pin_g, 0, 100), call(gpio_pin_b, 0, 100)]
        mock_wiringpi_softPwmCreate.assert_has_calls(calls)
        r_level = 1
        g_level = 2
        b_level = 3
        led.set(r_level, g_level, b_level)
        calls = [call(gpio_pin_r, r_level), call(gpio_pin_g, g_level), call(gpio_pin_b, b_level)]
        mock_wiringpi_softPwmWrite.assert_has_calls(calls)
        self.assertEqual(led.get(), (1, 2, 3))

    @patch('Adafruit_SSD1306.SSD1306_128_64')
    def test7_Display(self, mock_Adafruit_SSD1306, mock_wiringpi_ISR, mock_wiringpi_pinMode, \
            mock_wiringpi_setup):
        RESET_PIN = 4
        width = 200
        height = 100
# ensure mocked Adafruit driver has width and height properties
        instance = mock_Adafruit_SSD1306.return_value
        instance.width = width
        instance.height = height

        display = Display(RESET_PIN)
        mock_Adafruit_SSD1306.assert_called_with(rst=RESET_PIN)
        assert display.width == width
        assert display.height == height
        display.image(path.dirname(path.realpath(filename)) + "/volumio.ppm")

if __name__ == '__main__':
    unittest.main()
