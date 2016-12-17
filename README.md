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

# fonts
The [Pix Chicago](http://www.dafont.com/pix-chicago.font) font is provided by Etienne Desclides.
The [Bitstream Vera Sans]i(http://ftp.gnome.org/pub/GNOME/sources/ttf-bitstream-vera/1.10/) is one of the [Gnome fonts](https://www.gnome.org/fonts/)
