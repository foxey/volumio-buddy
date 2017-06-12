#!/usr/bin/python
# Copyright (c) 2016 Michiel Fokke
# Author: Michiel Fokke <michiel@fokke.org>
# vim: set ts=4 sw=4 expandtab si:

try:
    # Try using ez_setup to install setuptools if not already installed.
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Ignore import error and assume Python 3 which already has setuptools.
    pass

classifiers = ['Development Status :: 4 - Beta',
               'Operating System :: POSIX :: Linux',
               'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
               'Intended Audience :: End Users/Desktop',
               'Programming Language :: Python :: 2.7',
               'Topic :: Multimedia :: Sound/Audio',
               'Topic :: System :: Hardware']

from setuptools import setup, find_packages
setup(
    name="volumio-buddy",
    version="0.2.8",
    author="Michiel Fokke",
    author_email="michiel@fokke.org",
    description="A helper program for Volumio 2 hardware add-on's",
    license="GPL3",
    url="https://github.com/foxey/volumio-buddy/",
    keywords="Volumio Volumio2 GPIO SSD1306 OLED LED",
    packages=find_packages(),
    scripts=['volumio-buddy.py', 'volumio-buddy-display.py', 'volumio-buddy-buttons.py'],
    dependency_links  = ['https://github.com/adafruit/Adafruit_Python_SSD1306/tarball/master#egg=Adafruit_SSD1306-1.6.1'],
    install_requires  = ['RPi.GPIO>=0.6.3', 'Adafruit_SSD1306>=1.6.1', 'wiringpi2>=2.32', 'Pillow>=2.6.1', 'socketIO-client-2>=0.7.2'],
    tests_require = ['mock'],
    test_suite = 'tests',

    package_data={
        'volumio_buddy': ['*.ttf', '*.ppm'],
    },

)
