# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import unittest
import mock

from volumio_buddy import volumio_buddy_setup

@patch('wiringpi.wiringPiSetup')
def test_volumio_buddy_setup(mock_setup):
    volumio_buddy_setup()
    volumio_buddy_setup()
    mock_setup.assert_called_once_with()
