"""
Loosely based on the bluetoothMasterTest.py app from https://github.com/ShimmerResearch/tinyos-shimmer

We acquire data from the accelerometer and from the gyroscope modules on the mote, format them, and process
them via a process function. This approach can be used both for data to be locally transformed or for the data
to be forwarded to other apps (e.g. nodered)
"""

from collections import namedtuple
from threading import Thread
from typing import Callable
from bluetooth import *
import logging
import struct

__all__ = ["bt_init", "bt_listen", "bt_close", "DataTuple", "BTInputStream"]


# Standard bt service uuid and framesize in the tinyos Bluetooth implementation
# taken from the shimmer apps repo
_framesize = 22
_uuid = "85b98cdc-9f43-4f88-92cd-0c3fcf631d1d"


# This list contains a reference to each open connection
_open_conn = []

# Bluetooth server socket that acts as a slave for multiple
_bt_sock: BluetoothSocket

# Incoming data is stored in tuples
DataTuple = namedtuple("DataTuple", ["mac", "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"])
DataTuple.as_dict = DataTuple._asdict


def bt_init() -> None:
    """
    Initializes the bluetooth server socket interface.
    Call this at the beginning of your program.
    :return: None
    """
    global _bt_sock
    _bt_sock = BluetoothSocket(RFCOMM)
    _bt_sock.bind(("", PORT_ANY))
    _bt_sock.listen(1)
    advertise_service(_bt_sock, "BlRead", service_id=_uuid,
                      service_classes=[_uuid, SERIAL_PORT_CLASS], profiles=[SERIAL_PORT_PROFILE])


def bt_listen(process: Callable[[DataTuple], None]) -> None:
    """
    Starts the listen loop
    :param process: a void function taking in a DataTuple
    :return: None
    """
    while True:
        client_sock, client_info = _bt_sock.accept()
        logging.info(f"Mote connection with BT MAC: {client_info[0]}")
        in_stream = BTInputStream(mac=client_info[0], sock=client_sock, process=process)
        _open_conn.append(in_stream)
        in_stream.start()


def bt_close() -> None:
    """
    Gracefully stop any open connection
    :return: None
    """
    for in_stream in _open_conn:
        in_stream.stop()
    _bt_sock.close()


class BTInputStream(Thread):
    """
    Abstraction for the data input stream coming from a master device running
    on a shimmer2 mote.
    """
    def __init__(self, mac: str, sock: BluetoothSocket, process: Callable[[DataTuple], None]):
        """
        Initiaizes a new input stream

        :param mac: the BT MAC address of the mote sending data
        :param sock: the local socket bound to the mote
        :param process: a function that processes the generated DataTuples
        """
        super().__init__()
        self._mac = mac
        self._sock = sock
        self._running = False
        self._process = process

    def stop(self) -> None:
        """
        Stops the Input stream: N.B. if this is called while inside an iteration
        of the run method, that iteration won't be stopped
        :return: None
        """
        if self._running:
            self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            numbytes = 0
            ddata = bytearray()
            while numbytes < _framesize:
                ddata += bytearray(self._sock.recv(_framesize))
                numbytes = len(ddata)

            # the following data split refers to the 22 B long frame structure discussed earlier
            # the first seven and the last two fields (crc, end) are ignored since we don't need them
            # in this particular app
            data = ddata[0:_framesize]
            (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, _, _) = struct.unpack("HHHHHHHB", data[7:22])
            fmt_data = DataTuple(self._mac, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
            self._process(fmt_data)

        self._sock.close()
        _open_conn.remove(self)
