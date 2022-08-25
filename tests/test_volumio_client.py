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

import pytest
from .context import vb3


@pytest.fixture
def create_mock_coro(mocker, monkeypatch):
    def _create_mock_patch_coro(to_patch=None):
        mock = mocker.Mock()

        async def _coro(*args, **kwargs):
            return mock(*args, **kwargs)

        if to_patch:  # <-- may not need/want to patch anything
            monkeypatch.setattr(to_patch, _coro)
        return mock, _coro

    return _create_mock_patch_coro


@pytest.fixture
def mock_connect(create_mock_coro):
    # won't need the returned coroutine here
    mock, _ = create_mock_coro(to_patch="vb3.volumio_client.socketio.AsyncClient.connect")
    mock.return_value = None
    return mock


volumio = vb3.VolumioClient()
state = vb3.VolumioState()
handler_arg = [1]


def handler(arg):
    pass


def test_volumio_default_host():
    assert volumio.host == 'localhost'


def test_volumio_default_port():
    assert volumio.port == 3000


async def test_volumio_connect(mock_connect):
    await volumio.connect()
    assert mock_connect.call_count == 1


def test_volumio_set_pushState_handler():
    assert volumio.set_pushState_handler(handler, handler_arg) is None


def test_volumio_set_pushState_handler_exception():
    with pytest.raises(TypeError):
        volumio.set_pushState_handler(volumio, handler_arg)


def test_volumio_state():
    assert state.current['status'] == state.schema['status']['default']
    assert state.previous['status'] == state.schema['status']['default']
    assert state.changed('status') is False
    assert len(state.delta()) == 0


def test_volumio_state_update():
    state.update({'status': 'test'})
    assert state.current['status'] == 'test'
    assert state.previous['status'] == state.schema['status']['default']
    assert state.changed('status') is True
    assert len(state.delta()) == 1


def test_volumio_state_next_update():
    state.update({'status': 'next_test'})
    assert state.current['status'] == 'next_test'
    assert state.previous['status'] == 'test'
