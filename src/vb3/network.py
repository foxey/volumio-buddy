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

import socket


class Network(object):
    def __init__(self):
        self.hostapd = dict()
        self.wpa_supplicant = dict()
        try:
            file = open('/etc/hostapd/hostapd.conf')
            for line in file:
                try:
                    key, value = line.split('=')
                    self.hostapd[key] = value[:-1]
                except ValueError:
                    pass
        except IOError:
            pass
        try:
            self.hostapd['ssid']
        except KeyError:
            self.hostapd['ssid'] = 'unknown'
        try:
            self.hostapd['wpa_passphrase']
        except KeyError:
            self.hostapd['wpa_passphrase'] = 'unknown'
        try:
            file = open('/etc/wpa_supplicant/wpa_supplicant.conf')
            for line in file:
                try:
                    key, value = line.split('=')
                    self.wpa_supplicant[key] = value[:-1]
                except ValueError:
                    pass
        except IOError:
            pass
        try:
            self.wpa_supplicant['ssid']
        except KeyError:
            self.wpa_supplicant['ssid'] = 'unknown'
        try:
            self.wpa_supplicant['psk']
        except KeyError:
            self.wpa_supplicant['psk'] = 'unknown'

    def my_ip(self):
        try:
            return [line for line in
                    ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                     if not ip.startswith('127.')][:1],
                        [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close())
                          for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]])
                    if line][0][0]
        except Exception:
            return None
