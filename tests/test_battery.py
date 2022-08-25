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


battery = vb3.Battery()
callback_arg = [1]


def callback(arg):
    pass


@mock.patch('adafruit_ina219.INA219')
@mock.patch('board.I2C')
def test_ina219(mock_i2c, mock_ina219):
    assert mock_i2c.called_once()
    assert mock_ina219.called_once()


def test_battery_warn_function():
    assert battery.set_warn_function(callback, callback_arg) is None
    with pytest.raises(TypeError):
        battery.set_warn_function(battery, callback_arg)


def test_battery_empty_function():
    assert battery.set_empty_function(callback, callback_arg) is None
    with pytest.raises(TypeError):
        battery.set_empty_function(battery, callback_arg)
