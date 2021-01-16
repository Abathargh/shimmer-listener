from bluetooth.btcommon import BluetoothError
from typing import Callable, List, Dict, Any
from bluetooth import BluetoothSocket
from abc import ABC, abstractmethod
from collections import namedtuple
from threading import Thread, Lock
import logging
import struct


"""
Frame info: a frame may contain multiple "chunks"
    e.g. the SimpleAccel app sends frames of 120 B that contain 15 8 byte
        chunks of packed data with format "hhhh"
"""
frameinfo = namedtuple("frameinfo", ["framesize", "lenchunks", "format", "keys"])


# Incoming data if started as Slave is stored in tuples
SlaveDataTuple = namedtuple("DataTuple", ["mac", "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"])


def close_streams():
    for stream in _open_conn:
        if stream.open:
            stream.stop()


class BtStream(ABC, Thread):
    """
    Abstraction of a Bluetooth input stream coming from a mote with given mack
    over a given socket. Its data is processed by the given process function
    """
    def __init__(self, mac: str, sock: BluetoothSocket, process: Callable[[Dict], None]):
        """
        :param mac: the BT MAC address of the mote
        :param sock: the local socket bound to the mote
        :param process: a function that processes the generated DataTuples
        """
        super().__init__()
        self._mac = mac
        self._sock = sock
        self._running = False
        self._process = process

        with _mutex:
            _open_conn.append(self)

    @property
    def open(self) -> bool:
        """
        Property that returns True if the BtStream is still on
        :return: bool
        """
        return self._running

    def stop(self) -> None:
        """
        Stops the Input stream: N.B. if this is called while inside an iteration
        of the run method, that iteration won't be stopped
        :return: None
        """
        if self._running:
            self._running = False
            with _mutex:
                _open_conn.remove(self)

    @abstractmethod
    def run(self):
        pass


# This list contains a reference to each open connection
_open_conn: List[BtStream] = []
_mutex: Lock = Lock()


class BtMasterInputStream(BtStream):
    """
    Abstraction for the data input stream coming from a master device running
    on a shimmer2 mote.
    """

    # Standard framesize in the tinyos Bluetooth implementation taken from the shimmer apps repo
    _framesize = 22

    def __init__(self, mac: str, sock: BluetoothSocket, uuid: str, process: Callable[[Dict], None]):
        """
        Initializes a new input stream from a Master mote

        :param mac: the BT MAC address of the mote sending data
        :param sock: the local socket bound to the mote
        :param uuid: the uuid of the service that is being advertised
        :param process: a function that processes the generated DataTuples
        """
        super().__init__(mac=mac, sock=sock, process=process)
        self._uuid = uuid

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                numbytes = 0
                ddata = bytearray()
                while numbytes < self._framesize:
                    ddata += bytearray(self._sock.recv(self._framesize))
                    numbytes = len(ddata)

                # the following data split refers to the 22 B long frame structure discussed earlier
                # the first seven and the last two fields (crc, end) are ignored since we don't need them
                # in this particular app
                data = ddata[0:self._framesize]
                (accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, _, _) = struct.unpack("HHHHHHHB", data[7:22])
                fmt_data = SlaveDataTuple(self._mac, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
                self._process(fmt_data._asdict())
            except BluetoothError:
                break
        logging.info("Mote with BT MAC {}: disconnecting".format(self._mac))
        self._sock.close()


class BtSlaveInputStream(BtStream):
    """
    Abstraction for the data input stream coming from a slave device running
    on a shimmer2 mote.
    """

    """
    The first frame sent by the shimmer is special and contains information about its
    data format. The size is fixed by a simple protocol to 122 B.
    """
    fmt_frame_size = 112

    def __init__(self, mac: str, sock: BluetoothSocket, process: Callable[[Dict], None]):
        """
        Initializes a new input stream from a Master mote

        :param mac: the BT MAC address of the mote sending data
        :param sock: the local socket bound to the mote
        :param process: a function that processes the generated DataTuples
        """
        super().__init__(mac=mac, sock=sock, process=process)
        self._info = None

    def _to_dict(self, raw_data: tuple):
        d = {}
        for idx, key in enumerate(self._info.keys):
            d[key] = raw_data[idx]
        return d

    def _init_frameinfo(self, info: bytearray):
        fmt_unp = struct.unpack("BB10s100s", info)
        framesize = fmt_unp[0]
        lenchunks = fmt_unp[1]
        chunk_fmt = fmt_unp[2].decode().rstrip("\x00")

        unfmt_keys = fmt_unp[3].decode()
        data_keys = []

        key_len = 10
        keys_len = 100
        for base in range(0, keys_len, key_len):
            data_keys.append(unfmt_keys[base:base + key_len].rstrip("\x00"))
        data_keys = [elem for elem in data_keys if elem != '']
        self._info = frameinfo(framesize, lenchunks, chunk_fmt, data_keys)

    def run(self):
        self._running = True
        try:
            fmt_len = 0
            fmt_frame = bytearray()
            while fmt_len < BtSlaveInputStream.fmt_frame_size:
                fmt_frame += bytearray(self._sock.recv(BtSlaveInputStream.fmt_frame_size))
                fmt_len = len(fmt_frame)

            self._init_frameinfo(fmt_frame)
            logging.info(f"Received presentation frame: {self._info}")
        except struct.error:
            logging.error("error in decoding presentation frame!")
            self._running = False

        while self._running:
            data_len = 0
            data = bytearray()
            while data_len < self._info.framesize:
                data += bytearray(self._sock.recv(self._info.framesize))
                data_len = len(data)
            for idx in range(0, self._info.framesize, self._info.lenchunks):
                raw_data = struct.unpack(self._info.format, data[idx:idx + self._info.lenchunks])
                self._process(self._to_dict(raw_data))
        logging.info("Mote with BT MAC {}: disconnecting".format(self._mac))
        self._sock.close()
