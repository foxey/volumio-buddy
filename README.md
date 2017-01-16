![build status](https://travis-ci.org/foxey/volumio-buddy.svg?branch=master)

# volumio-buddy

Volumio-buddy is a python library and helper program for Volumio 2.
It is meant to run on the same host where the Volumio back-end runs and provides the following additional functionality:
- connect to volumio using the [websockets API](https://volumio.github.io/docs/API/WebSocket_APIs.html)
- support for GPIO pushbuttons to control volumio
- support for a rotary encoder to skip through a playlist
- support for a rotary encoder to adjust the volume
- RGB LED support
- SSD1306 OLED 128x64px screen support (I2C)

## dependencies
- [socketIO-client-2](https://pypi.python.org/pypi/socketIO-client-2)
- [WiringPI](http://wiringpi.com/)
- [PIL](http://effbot.org/zone/pil-index.htm)
- [Adafruit Python SSD1306](https://github.com/adafruit/Adafruit_Python_SSD1306)
- [RPi.GPIO](https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/) This package is a dependency of [Adafruit_Python_GPIO](https://github.com/adafruit/Adafruit_Python_GPIO) which is a dependency of Adafruit_Python_SSD1306, but is not listed in setup.py

## fonts
The [Pix Chicago](http://www.dafont.com/pix-chicago.font) font is provided by Etienne Desclides.

The [Bitstream Vera Sans](http://ftp.gnome.org/pub/GNOME/sources/ttf-bitstream-vera/1.10/) is one of the [Gnome fonts](https://www.gnome.org/fonts/).

## install
First, ensure you have JPEG and Freetype support libraries installed:

	apt-get install -y libjpeg9-dev libfreetype6-dev

After that, clone the github repository:

	git clone https://github.com/foxey/volumio-buddy
	cd volumio-buddy

Then install the library and the script:

	python ./setup.py install

Run the script:

	volumio-buddy.py
