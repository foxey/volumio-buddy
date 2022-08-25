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

import argparse
import asyncio
import functools
import logging
import signal
from .display import Display


def argparser():
    parser = argparse.ArgumentParser(
        description='Volumio buddy integrates hardware add-ons.')
    parser.add_argument('-l', '--log', action='store', type=str,
                        choices=['debug', 'info', 'warning', 'error', 'critical'],
                        default='warning')
    parser.add_argument('-p', '--pull', action='store', type=str,
                        choices=['none', 'up', 'down'],
                        default='none')
    return vars(parser.parse_args())


def handle_exception(volumio_client, display, loop, context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])
    logging.error(f"Caught exception: {msg}")
    logging.info("Shutting down...")
    asyncio.create_task(shutdown(volumio_client, display, loop))


async def shutdown(volumio_client, display, loop, signal=None):
    """Cleanup tasks tied to the service's shutdown."""
    if signal:
        logging.info(f"Received exit signal {signal.name}...")

    if display:
        display.status(Display.STATUS_SHUTDOWN)
        display.update()

    if volumio_client.is_connected():
        logging.info('Disconnecting websocket connection.')
        try:
            await volumio_client.disconnect()
        except Exception:
            logging.info('Failed to disconnect websocket.')
            pass

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        [task.cancel() for task in tasks]
        logging.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        if display:
            await asyncio.sleep(3)

    if display:
        display.clear()

    loop.stop()


def setup_exception_handling(volumio_client, display, loop):

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(volumio_client, display, loop, signal=s)))
        logging.info(f'Added signal handler for {s.name} signal')
    exception_handler = functools.partial(handle_exception, volumio_client, display)
    loop.set_exception_handler(exception_handler)


def setup_logging(log_level):
    log_level_num = getattr(logging, log_level.upper(), None)
    if not isinstance(log_level_num, int):
        raise ValueError('Invalid log level: %s' % log_level)
    FORMAT = "%(asctime)s - %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
    logging.basicConfig(level=log_level_num, format=FORMAT)
    logging.info('Logging on {} ({}) level.'.format(log_level.upper(), log_level_num))
