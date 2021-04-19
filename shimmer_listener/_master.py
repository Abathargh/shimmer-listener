"""
General idea:
- A thread keeps searching for bluetooth slaves that can be shimmer devices (*)
- When it finds 1+, it tries to pair with them, if it manages to, it spawns
    a new thread that manages the data transfer for that node.

(*) devices with an ID starting with "RN42" are shimmer devices
"""

from typing import Optional, Callable, Any, Dict
from threading import Lock
import bluetooth
import logging
import time

from ._streams import BtSlaveInputStream, Frameinfo

# Lookup duration for the scan operation by the master
# The RF port to use is the number 1
lookup_duration = 5
scan_interval = 5


# App name to frameinfo mapping
_discovering = True


# This list contains a reference to each open connection
_open_conn: Dict[str, BtSlaveInputStream] = {}
_mutex = Lock()


def _close_stream(mac: str):
    with _mutex:
        _open_conn.pop(mac, None)


def _close_streams():
    for _, stream in _open_conn.items():
        if stream.open:
            stream.stop()


def _master_listen(connect_handle: Optional[Callable[[str, Frameinfo], None]] = None,
                   message_handle: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                   disconnect_handle: Optional[Callable[[str, bool], None]] = None) -> None:
    # We need to add a way to delete the stream from the open ones when it disconnects, so
    # we modify the passed disconnect handler to have a call to the local private _close_stream
    def capture_disconnect(mac, lost):
        if disconnect_handle:
            disconnect_handle(mac, lost)
        _close_stream(mac)

    while _discovering:
        # flush_cache=True, lookup_class=False possible fix to script as exec bug?
        found_devices = bluetooth.discover_devices(duration=lookup_duration, lookup_names=True)
        for device in found_devices:
            logging.info(f"Found device with MAC {device[0]}, ID {device[1]}")
            if _is_shimmer_device(device[1]):
                try:
                    if device[0] not in _open_conn:
                        logging.info(f"Pairing with {device[0]}..")
                        in_stream = BtSlaveInputStream(mac=device[0])
                        in_stream.on_connect = connect_handle
                        in_stream.on_message = message_handle
                        in_stream.on_disconnect = capture_disconnect
                        in_stream.start()
                        with _mutex:
                            _open_conn[device[0]] = in_stream
                except bluetooth.btcommon.BluetoothError as err:
                    logging.error(err)
        time.sleep(scan_interval)


def _master_close():
    global _discovering
    _discovering = False
    _close_streams()


def _is_shimmer_device(bt_id: str) -> bool:
    return bt_id.startswith("RN42")
