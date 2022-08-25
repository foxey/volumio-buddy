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
import board
import adafruit_ina219


class Battery:
    CELL_COUNT = 5
    FULL = 4.2  # Maximum voltage of a 18650 LiPo Cell
    LOW = 2.9
    WARN = 3.2
    EMPTY = 2.8

    def __init__(self, i2c_addr=None):
        i2c_bus = board.I2C()
        if i2c_addr:
            self._ina = adafruit_ina219.INA219(i2c_bus, addr=i2c_addr)
        else:
            self._ina = adafruit_ina219.INA219(i2c_bus)
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
        return self._ina.shunt_voltage + self._ina.bus_voltage

    def level(self):
        return int(100*(self.voltage()/self.cell_count-self.low)/(self.full-self.low))

    def set_warn_function(self, function, *args):
        if not callable(function):
            raise TypeError('Argument for warn function is not a function, but a {}.'
                            .format(type(function)))
        self._warn_function = function
        self._warn_function_args = args

    def set_empty_function(self, function, *args):
        if not callable(function):
            raise TypeError('Argument for empty function is not a function, but a {}.'
                            .format(type(function)))
        self._empty_function = function
        self._empty_function_args = args

    async def monitor(self, polling_interval=10):
        logging.info('started battery polling task')
        while True:
            voltage = self.voltage()
            if voltage <= self.cell_count*self.warn and self._warn_function:
                logging.warning('Battery._monitor: call _warn_function (v=%.3f)' % voltage)
                self._warn_function(*self._warn_function_args)
            if voltage <= self.cell_count*self.EMPTY and self._empty_function:
                logging.warning('Battery._monitor: call _empty_function (v=%.3f)' % voltage)
                self._empty_function(*self._empty_function_args)
            await asyncio.sleep(polling_interval)
