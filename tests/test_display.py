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


def arg_func_1():
    return 'string_1'


def arg_func_2():
    return 'string_2'


def arg_func_3():
    return 'string_3'


def arg_func_4():
    return 4


def arg_func_5():
    return [1, 2, 3, 4, 5]


@mock.patch('adafruit_ssd1306.SSD1306_I2C')
@mock.patch('busio.I2C')
def test_display(mock_i2c, mock_ssd1306):
    mock_ssd1306().width = 128
    mock_ssd1306().height = 64
    display = vb3.Display()
    assert mock_i2c.called_once()
    assert mock_ssd1306.called_once()
    assert display.width == 128
    assert display.height == 64


@mock.patch('adafruit_ssd1306.SSD1306_I2C')
@mock.patch('busio.I2C')
def test_display_show(mock_i2c, mock_ssd1306):
    mock_ssd1306().width = 128
    mock_ssd1306().height = 64
    display = vb3.Display()
    display.show(display._image)
    assert display._display.image.called_once()
    assert display._display.show.called_once()


@mock.patch('busio.I2C')
def test_modal(mock_i2c):
    display = vb3.Display()
    modal = vb3.display.Modal(display._image)
    assert type(modal.image()).__name__ == 'Image'


@mock.patch('busio.I2C')
def test_text_modal(mock_i2c):
    display = vb3.Display()
    modal = vb3.display.TextModal(display._image, display._font, 'test')
    assert type(modal.image()).__name__ == 'Image'


@mock.patch('busio.I2C')
def test_two_line_text_modal(mock_i2c):
    display = vb3.Display()
    modal = vb3.display.TwoLineTextModal(display._image, display._font, ('test', 'test'))
    assert type(modal.image()).__name__ == 'Image'


@mock.patch('busio.I2C')
def test_two_line_text_modal_exception(mock_i2c):
    display = vb3.Display()
    with pytest.raises(TypeError):
        vb3.display.TwoLineTextModal(display._image, display._font, 'test')


@mock.patch('busio.I2C')
def test_bar_modal(mock_i2c):
    display = vb3.Display()
    modal = vb3.display.BarModal(display._image, display._font, 'test', 50)
    assert type(modal.image()).__name__ == 'Image'


@mock.patch('busio.I2C')
def test_bar_modal_exception(mock_i2c):
    display = vb3.Display()
    with pytest.raises(ValueError):
        vb3.display.BarModal(display._image, display._font, 'test', -1)


@mock.patch('busio.I2C')
def test_scrollable_text(mock_i2c):
    display = vb3.Display()
    scollable_text = vb3.display.ScrollableText('test', display._font)
    assert type(scollable_text._image).__name__ == 'Image'


@mock.patch('busio.I2C')
def test_scrollable_text_draw(mock_i2c):
    display = vb3.Display()
    scrollable_text = vb3.display.ScrollableText('test', display._font)
    scrollable_text.draw(display._image, (0, 0), 0)
    assert type(scrollable_text._image).__name__ == 'Image'


def test_popup_with_string():
    popup = vb3.Popup('{}', 'string_1')
    assert popup.label() == 'string_1'


def test_popup_with_function_returning_int():
    popup = vb3.Popup('{}', arg_func_4)
    assert popup.label() == '4'


def test_popup_with_function_returning_list():
    popup = vb3.Popup('{}', arg_func_5)
    assert popup.label() == '[1, 2, 3, 4, 5]'


def test_popup_with_two_functions():
    popup = vb3.Popup('{} {}', arg_func_1, arg_func_2)
    assert popup.label() == 'string_1 string_2'


def test_popup_with_two_functions_and_tuple_textlabel():
    popup = vb3.Popup(('{}', '{}'), arg_func_1, arg_func_2)
    assert popup.label() == ('string_1', 'string_2')


def test_popup_with_three_functions_and_tuple_textlabel():
    popup = vb3.Popup(('{} {}', '{}'), arg_func_1, arg_func_2, arg_func_3)
    assert popup.label() == ('string_1 string_2', 'string_3')


def test_popup_with_three_functions_and_another_tuple_textlabel():
    popup = vb3.Popup(('{}', '{} {}'), arg_func_1, arg_func_2, arg_func_3)
    assert popup.label() == ('string_1', 'string_2 string_3')


def test_popup_with_function_with_():
    popup = vb3.Popup('{} {}', arg_func_1, arg_func_2)
    assert popup.label() == 'string_1 string_2'


def test_popup_invalid_labeltext():
    with pytest.raises(vb3.display.InvalidLabelError):
        vb3.Popup(1)


def test_popup_with_too_much_placeholders():
    with pytest.raises(vb3.display.LabelArgsMismatchException):
        vb3.Popup('{} {}', arg_func_1)


def test_popup_with_invalid_arg():
    with pytest.raises(TypeError):
        vb3.Popup('{}', 1)
