#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

import time
from volumio_buddy import RotaryEncoder, Display, ScrollableText
from PIL import Image
from PIL import ImageFont
RESET_PIN = 26

display = Display(RESET_PIN)

# Initialize library.
display.clear()

label1='very long text that does not fit on the screen'
label2='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed consequat id augue ac sollicitudin. Fusce quis cursus est. Nam volutpat eros faucibus consequat euismod. Integer ac imperdiet justo, non malesuada nisi. Nam bibendum urna sed bibendum auctor. Ut gravida ipsum quis justo luctus, consectetur malesuada sem rhoncus. In ac urna.'
label3='short text'

image = Image.new('1', (display.width, display.height))
font = ImageFont.truetype('pixChicago.ttf', 10)

scrollable1 = ScrollableText(label1, font)
scrollable2 = ScrollableText(label2, font)
scrollable3 = ScrollableText(label3, font)

try:
    while True:
#        for i in range(0, 5*int((scrollable2.textwidth-width)/5)+8, 10):
        for i in range(0, int(1e6), 10):
            scrollable1.draw(image, (0,0), i)
            scrollable2.draw(image, (0,scrollable1.textheight+4), i)
            scrollable3.draw(image, (0,scrollable1.textheight+scrollable2.textheight+8), i)
            display._modal_timeout = time.time()+1
            display.display(image)
            time.sleep(.3)

finally:
# Clear the screen after pressing ^C
    display.clear()
