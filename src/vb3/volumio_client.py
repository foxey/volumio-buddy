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
import socketio


class ConnectionError(Exception):
    def __init__(self, message='Can\'t connect to Volumio websocket.'):
        self.message = message
        super().__init__(self, message)

    def __str__(self):
        return f'{self.message}'


class NotConnectedException(Exception):
    def __init__(self, message='Not connected. Can\'t disconnect.'):
        self.message = message
        super().__init__(self, message)

    def __str__(self):
        return f'{self.message}'


class VolumioClient:
    """ Websocket client to control and get updates from Volumio """
    def __init__(self, display=None, host='localhost', port=3000):
        self._display = display
        self.host = host
        self.port = port
        self._pushState_handler = None
        self._pushState_handler_args = None
        self.state = VolumioState()
        self._sio = socketio.AsyncClient()
        self._loop = None
        self._tries = 0
        self._max_tries = 5

        @self._sio.event
        async def connect():
            logging.info('Connected to Volumio websocket with sid {}'
                         .format(self._sio.sid))
            await self._sio.emit('getState')

        @self._sio.event
        async def connect_error(data):
            logging.error('The Volumio websocket connection failed!')
            if self._tries == self._max_tries:
                raise ConnectionError('Can\'t connect to Volumio websocket. '
                                      'Giving up after {} tries'.format(self._tries))
            await self._connect()

        @self._sio.event
        async def disconnect():
            if self._display:
                self._display.status(self._display.STATUS_RECONNECTING)
            logging.info('Volumio websocket disconnected.')

        @self._sio.event
        async def pushState(*data):
            logging.info('pushState message received')
            logging.debug('\twith data:\n  {}'.format(data[0]))
            self.state.update(data[0])
            if self._pushState_handler and self.state.delta():
                self._pushState_handler(*self._pushState_handler_args)

    def set_pushState_handler(self, handler_function, *handler_args):
        if not callable(handler_function):
            raise TypeError('Argument for handler function is not a function, '
                            'but a {}.'.format(type(handler_function)))
        self._pushState_handler = handler_function
        self._pushState_handler_args = handler_args

    async def connect(self):
        await self._connect()
        self._loop = asyncio.get_running_loop()

    async def _connect(self):
        self._tries += 1
        if self._display:
            self._display.status(self._display.STATUS_CONNECTING)
        result, *_ = await asyncio.gather(self._sio.connect(
            'http://{}:{}'.format(self.host, self.port)),
            return_exceptions=True)
        if result:
            logging.warning('{} (try {} of {})'.format(result, self._tries,
                                                       self._max_tries))
            await asyncio.sleep(2)

    def is_connected(self):
        return self._sio.connected

    def play(self):
        if self._sio.connected:
            asyncio.run_coroutine_threadsafe(self._sio.emit('play'), self._loop)

    def pause(self):
        if self._sio.connected:
            asyncio.run_coroutine_threadsafe(self._sio.emit('pause'), self._loop)

    def prev(self):
        if self._sio.connected:
            asyncio.run_coroutine_threadsafe(self._sio.emit('prev'), self._loop)

    def next(self):
        if self._sio.connected:
            asyncio.run_coroutine_threadsafe(self._sio.emit('next'), self._loop)

    def toggle_play(self):
        if 'status' in self.state.current.keys() and self.state.current['status'] == 'play':
            return self.pause()
        else:
            return self.play()

    def volume_up(self):
        if self._sio.connected:
            asyncio.run_coroutine_threadsafe(self._sio.emit('volume', '+'), self._loop)

    def volume_down(self):
        if self._sio.connected:
            asyncio.run_coroutine_threadsafe(self._sio.emit('volume', '-'), self._loop)

    async def disconnect(self):
        if self._sio.connected:
            await self._sio.disconnect()
        else:
            raise NotConnectedException


class VolumioState():
    """ Helper to sanitize the pushState message"""

    schema = {
        'album' : {'transform': str, 'default' : ''},
        'albumart' : {'transform': str, 'default' : ''},
        'artist' : {'transform': str, 'default' : ''},
        'bitdepth': {'transform': str, 'default' : ''},
        'bitrate': {'transform': str, 'default' : ''},
        'channels': {'transform': int, 'default' : 0},
        'consume' : {'transform': bool, 'default' : ''},
        'dbVolume' : {'transform': bool, 'default' : False},
        'disableVolumeControl' : {'transform': bool, 'default' : False},
        'duration' : {'transform': int, 'default' : 0},
        'mute' : {'transform': bool, 'default' : False},
        'position' : {'transform': int, 'default' : 0},
        'random' : {'transform': bool, 'default' : False},
        'repeat' : {'transform': bool, 'default' : False},
        'repeatSingle' : {'transform': bool, 'default' : False},
        'samplerate': {'transform': str, 'default' : ''},
        'seek' : {'transform': lambda s: int(s/1000), 'default' : 0},
        'service' : {'transform': str, 'default' : ''},
        'status' : {'transform': str, 'default' : 'stop'},
        'stream' : {'transform': str, 'default' : ''},
        'title' : {'transform': str, 'default' : ''},
        'trackType' : {'transform': str, 'default' : ''},
        'updatedb' : {'transform': bool, 'default' : False},
        'uri' : {'transform': str, 'default' : ''},
        'volatile' : {'transform': bool, 'default' : False},
        'volume' : {'transform': int, 'default' : 0},
    }

    def __init__(self, state=dict()):
        self.current = dict()
        self.update(state)
        self.previous = self.current

    def sanitize(self, in_state):
        out_state = dict()
        for key in self.schema.keys():
            try:
                out_state[key] = self.schema[key]['transform'](in_state[key])
            except (KeyError, TypeError, ValueError) as exception:
                logging.debug('{} for key \'{}\', using default'.format(type(exception), key))
                out_state[key] = self.schema[key]['default']
        return out_state

    def update(self, state):
        self.previous = self.current
        self.current = self.sanitize(state)
        return self.current

    def changed(self, key):
        if (self.current[key] != self.previous[key]):
            return True
        else:
            return False

    def delta(self):
        delta = dict()
        for key in self.current.keys():
            if self.current[key] != self.previous[key]:
                delta[key] = self.current[key]
        return delta

    def get(self, key):
        if key in self.current.keys():
            return self.current[key]
