
![build status](https://github.com/foxey/volumio-buddy/actions/workflows/python-package.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/volumio-buddy.svg)](https://pypi.python.org/pypi/volumio-buddy)

# volumio-buddy

# new release!

This release now supports Volumio 3! It's actually an almost complete rewrite of the code, now using Python 3 with asyncio. It doesn't support Volumio 2 anymore, because the underlying OS is too outdated for a smooth migration to Python 3 (Volumio 2 users can still use release 0.4.1).

## Introduction

Volumio-buddy is a python3 library and helper program for Volumio 3.
It is meant to run on the same host where the Volumio back-end runs and provides the following additional functionality:
- connect to volumio using the [websockets API](https://volumio.github.io/docs/API/WebSocket_APIs.html)
- support for GPIO pushbuttons to control volumio
- support for [rotary encoders](https://en.wikipedia.org/wiki/Incremental_encoder) to adjust the volume and to skip through a playlist
- RGB LED support
- [SSD1306 OLED](https://learn.adafruit.com/monochrome-oled-breakouts/arduino-library-and-examples) 128x64px screen support (I2C)
- Battery power monitoring with an [INA219](https://learn.adafruit.com/adafruit-ina219-current-sensor-breakout) chip.

## Installation instructions

The package assumes installation on a Debian based distribution for Raspberry Pi with `systemd` based init. If you don't use `systemd`, install the package with `make install` and start the `vbuddy` script manually in the virtual environment.

Edit `src/vbuddy` to reflect your hardware setup. The script ignores the display and battery  monitoring components if they are not found, but you need to update the GPIO pin configuration and the I2C addresses, if you use different ones than I do.

If your buttons or rotary encoders need an internal pullup or pulldown resistor, edit `src/vbuddy.service` to include the commandline option `-p up` or `-p down` in the `ExecStart` line.

Install the service in a separate virtual environment using the following commands:

```
make .venv
. .venv/bin/activate
make service
sudo systemctl start vbuddy
```