from collections import namedtuple
from typing import Dict, Callable
import bluetooth
import logging
import time

from ._streams import BtSlaveInputStream, frameinfo

"""
General idea:
    - A thread keep searching for bluetooth slaves that can be shimmer devices
    - When it finds 1+, it tries to pair with them, if it manages to, it spawns 
        a new thread that manages the data transfer for that node ~ InputStream of Master ifc
"""

# found devices => list(devices), where device is a tuple (BT MAC, Slave ID)
# devices with an ID starting with "RN42" are shimmer devices

# Lookup duration for the scan operation by the master
# The RF port to use is the number 1
lookup_duration = 5
rf_port = 1


# App name to frameinfo mapping
_current_app: str
_discovering = True


# require formatting in app init and store nothing in hardcoded way

_apps: Dict[str, frameinfo] = {
    "simple_accel": frameinfo(120, 8, "hhhh", ["accel_x", "accel_y", "accel_z", "rawbatt"])
}


def _master_init(node_app: str):
    global _current_app
    if node_app is None or node_app not in _apps:
        raise ValueError("Invalid node_app passed to the init function")
    _current_app = node_app


def _master_listen(process: Callable[[namedtuple], None]) -> None:
    global _discovering
    while _discovering:
        # flush_cache=True, lookup_class=False possible fix to script as exec bug?
        found_devices = bluetooth.discover_devices(duration=lookup_duration, lookup_names=True)
        for device in found_devices:
            bluetooth.BluetoothSocket()
            logging.info(f"Found device with MAC {device[0]}, ID {device[1]}")
            if _is_shimmer_device(device[1]):
                try:
                    logging.info(f"Pairing with {device[0]}..")
                    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                    sock.connect((device[0], rf_port))
                    BtSlaveInputStream(mac=device[0], sock=sock, process=process, app_info=_apps[_current_app]).start()
                except bluetooth.btcommon.BluetoothError as err:
                    logging.error(err)
        time.sleep(5)


def _master_close():
    global _discovering
    _discovering = False


def _is_shimmer_device(bt_id: str) -> bool:
    return bt_id.startswith("RN42")
