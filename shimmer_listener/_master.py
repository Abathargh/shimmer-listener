"""
General idea:
- A thread keeps searching for bluetooth slaves that can be shimmer devices (*)
- When it finds 1+, it tries to pair with them, if it manages to, it spawns
    a new thread that manages the data transfer for that node.

(*) devices with an ID starting with "RN42" are shimmer devices
"""

from typing import Optional, Callable, Any, Dict
import bluetooth
import logging
import time

from ._streams import BtSlaveInputStream, frameinfo

# Lookup duration for the scan operation by the master
# The RF port to use is the number 1
lookup_duration = 5
scan_interval = 5


# App name to frameinfo mapping
_discovering = True


def _master_listen(connect_handle: Optional[Callable[[str, frameinfo], None]] = None,
                   message_handle: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                   disconnect_handle: Optional[Callable[[str, bool], None]] = None) -> None:
    while _discovering:
        # flush_cache=True, lookup_class=False possible fix to script as exec bug?
        found_devices = bluetooth.discover_devices(duration=lookup_duration, lookup_names=True)
        for device in found_devices:
            logging.info(f"Found device with MAC {device[0]}, ID {device[1]}")
            if _is_shimmer_device(device[1]):
                try:
                    logging.info(f"Pairing with {device[0]}..")
                    in_stream = BtSlaveInputStream(mac=device[0])
                    in_stream.on_connect = connect_handle
                    in_stream.on_message = message_handle
                    in_stream.on_disconnect = disconnect_handle
                    in_stream.start()
                except bluetooth.btcommon.BluetoothError as err:
                    logging.error(err)
        time.sleep(scan_interval)


def _master_close():
    global _discovering
    _discovering = False


def _is_shimmer_device(bt_id: str) -> bool:
    return bt_id.startswith("RN42")
