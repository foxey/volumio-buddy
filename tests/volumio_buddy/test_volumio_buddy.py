# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import unittest
try:
    import mock
    from mock import patch
except ImportError:
    from unittest import mock
    from unittest.mock import patch
import wiringpi

from volumio_buddy import volumio_buddy_setup, PushButton

@patch('wiringpi.wiringPiSetup', autospec=True)
@patch('wiringpi.pinMode', autospec=True)
@patch('wiringpi.wiringPiISR', autospec=True)

class TestVolumioBuddy(unittest.TestCase):
        
    def test0_volumio_buddy_setup(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        volumio_buddy_setup()
        volumio_buddy_setup()
        mock_wiringpi_setup.assert_called_once_with()

    def test1_PushButton(self, mock_wiringpi_ISR, mock_wiringpi_pinMode, mock_wiringpi_setup):
        def callback_function():
            pass
        gpio_pin = 1
        p = PushButton(gpio_pin)
        mock_wiringpi_pinMode.assert_called_with(gpio_pin, 0)
        p.set_callback(callback_function)
        mock_wiringpi_ISR.assert_called_with(gpio_pin, wiringpi.INT_EDGE_BOTH, p._callback)

if __name__ == '__main__':
    unittest.main()
