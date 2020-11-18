from typing import Callable, Dict
from bluetooth import *
import logging

from ._streams import BtMasterInputStream

# Standard bt service uuid taken from the bluetoothMaster repo
_uuid = "85b98cdc-9f43-4f88-92cd-0c3fcf631d1d"

# Bluetooth server socket that acts as a slave for multiple
_bt_sock: BluetoothSocket


def _slave_init():
    global _bt_sock
    _bt_sock = BluetoothSocket(RFCOMM)
    _bt_sock.bind(("", PORT_ANY))
    _bt_sock.listen(1)
    advertise_service(_bt_sock, "BlRead", service_id=_uuid,
                      service_classes=[_uuid, SERIAL_PORT_CLASS], profiles=[SERIAL_PORT_PROFILE])


def _slave_listen(process: Callable[[Dict], None]):
    global _bt_sock
    while True:
        client_sock, client_info = _bt_sock.accept()
        logging.info("Mote connection with BT MAC: {}".format(client_info[0]))
        in_stream = BtMasterInputStream(mac=client_info[0], sock=client_sock, uuid=_uuid, process=process)
        in_stream.start()


def _slave_close():
    _bt_sock.close()
