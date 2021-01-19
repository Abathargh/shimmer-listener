"""
Loosely based on the bluetoothMasterTest.py app from https://github.com/ShimmerResearch/tinyos-shimmer

We acquire data from the accelerometer and from the gyroscope modules on the mote, format them, and process
them via a process function. This approach can be used both for data to be locally transformed or for the data
to be forwarded to other apps (e.g. nodered)

This library is mainly used in master mode and its slave mode functionalities are limited to the bluetoothMasterApp.
"""

from typing import Optional, Callable, Any, Dict
from bluetooth import *
import logging

from ._streams import BtMasterInputStream, frameinfo

# Bluetooth server socket that acts as a slave for multiple
_bt_sock: BluetoothSocket

# Standard bt service uuid taken from the bluetoothMaster repo
_uuid = "85b98cdc-9f43-4f88-92cd-0c3fcf631d1d"


def _slave_init():
    global _bt_sock
    _bt_sock = BluetoothSocket(RFCOMM)
    _bt_sock.bind(("", PORT_ANY))
    _bt_sock.listen(1)
    advertise_service(_bt_sock, "BlRead", service_id=_uuid,
                      service_classes=[_uuid, SERIAL_PORT_CLASS], profiles=[SERIAL_PORT_PROFILE])


def _slave_listen(connect_handle: Optional[Callable[[str, frameinfo], None]] = None,
                  message_handle: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                  disconnect_handle: Optional[Callable[[str, bool], None]] = None) -> None:
    global _bt_sock
    while True:
        client_sock, client_info = _bt_sock.accept()
        logging.info("Mote connection with BT MAC: {}".format(client_info[0]))
        in_stream = BtMasterInputStream(mac=client_info[0], sock=client_sock, uuid=_uuid)
        in_stream.on_connect = connect_handle
        in_stream.on_message = message_handle
        in_stream.on_disconnect = disconnect_handle
        in_stream.start()


def _slave_close():
    _bt_sock.close()
