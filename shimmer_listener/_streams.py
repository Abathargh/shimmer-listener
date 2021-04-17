from typing import Optional, Callable, Dict, Any
from abc import ABC, abstractmethod
from collections import namedtuple
from threading import Thread
import bluetooth
import struct


class Frameinfo(namedtuple("frameinfo", ["framesize", "lenchunks", "format", "keys"])):
    """A description of the format used by the shimmer device to communicate. The data received through the
    presentation protocol at startup is contained in an instance of this class."""
    pass


SlaveDataTuple = namedtuple("DataTuple", ["mac", "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"])
"""Incoming data format for the only slave app supported"""


class BtStream(ABC):
    """
    Abstraction of a Bluetooth input stream coming from a mote with given mac over a given socket.
    A series of callbacks can be used and set as properties to intercept certain events:

    - **on_connect(mac: str, info: frameinfo) -> None**

        Called when a mote identified by **mac** succesfully connects. All the information
        regarding the exchanged data format, obtained through *the presentatin protocol* are
        accessible via **info**.

    - **on_message(mac: str, frame: Dict[str, Any]) -> None**

        Called when a message is received from a mote identified by **mac**. The message is
        returned as a dict with the keys previously obtained from the *presentation protocol*.

    - **on_disconnect(mac: str, lost: bool) -> None**

        Called when a mote identified by **mac** disconnects. If **lost** is true, the disconnect
        event happened because the connection has been lost.
    """

    def __init__(self, mac: str):
        """
        Abstract class that describes and implements common functionalities of the Bt streams: the start/stop
        mechanism, callbacks, identification via Bt mac address.
        """
        super().__init__()
        self._mac = mac
        self._running = False

        # Callbacks
        self._on_connect: Optional[Callable[[str, Frameinfo], None]] = None
        self._on_message: Optional[Callable[[str, Dict[str, Any]], None]] = None
        self._on_disconnect: Optional[Callable[[str, bool], None]] = None

    @property
    def on_connect(self):
        return self._on_connect

    @on_connect.setter
    def on_connect(self, callback):
        self._on_connect = callback

    @property
    def on_message(self):
        return self._on_message

    @on_message.setter
    def on_message(self, callback):
        self._on_message = callback

    @property
    def on_disconnect(self):
        return self._on_disconnect

    @on_disconnect.setter
    def on_disconnect(self, callback):
        self._on_disconnect = callback

    @property
    def open(self) -> bool:
        """
        Property that is True if the BtStream was started and is currently active.
        """
        return self._running

    def stop(self) -> None:
        """
        Stops the Input stream: N.B. if this is called while when the stream loop is doing work,
        that iteration of the loop won't be stopped.
        """
        if self._running:
            self._running = False

    @abstractmethod
    def _loop(self):
        pass

    def start(self):
        """
        Starts the Input stream, non blocking.
        """
        if not self._running:
            Thread(target=self._loop).start()


class BtMasterInputStream(BtStream):
    """
    Abstraction for the data input stream coming from a master device running
    on a shimmer2 mote.
    """

    # Standard framesize in the tinyos Bluetooth implementation taken from the shimmer apps repo
    # In this case a frame contains exactly one chunk, hence framesize = chunklen
    _framesize = 22
    _slave_frameinfo = Frameinfo(_framesize, _framesize, "HHHHHHHB",
                                 ["mac", "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"])

    def __init__(self, mac: str, sock: bluetooth.BluetoothSocket, uuid: str):
        """
        Initializes a new input stream from a Master mote.
        """
        super().__init__(mac=mac)
        self._uuid = uuid
        self._sock = sock

    def _loop(self) -> None:
        if self.on_connect:
            self.on_connect(self._mac, self._slave_frameinfo)

        self._running = True
        try:
            while self._running:
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
                if self.on_message:
                    self.on_message(self._mac, fmt_data._asdict())
            if self.on_disconnect:
                self.on_disconnect(self._mac, False)
        except bluetooth.btcommon.BluetoothError:
            if self.on_disconnect:
                self.on_disconnect(self._mac, True)
        finally:
            self._running = False
            self._sock.close()


class BtSlaveInputStream(BtStream):
    """
    Abstraction for the data input stream coming from a slave device running on a shimmer2 mote.

    The first frame sent by the shimmer is special and contains information about its
    data format. The size is fixed by a simple protocol to 112 B. Its internal format
    is made as such:

    - 1 unsigned byte containing the message frame size that is going to be used in the communication.
    - 1 unsigned byte containing the chunk size of each chunk packed into a frame.
    - a string of length 10, containing the format of packed data contained in each chunk.
    - a string of length 100, containing a max of 10, 10 char long key names of each value packed in the chunk.
    """
    _pres_frame_size = 112
    _pres_frame_fmt = "BB10s100s"

    def __init__(self, mac: str):
        """
        Initializes a new input stream from a Master mote.
        """
        super().__init__(mac=mac)
        self._info = None
        self._sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    def _to_dict(self, raw_data: tuple):
        d = {}
        for idx, key in enumerate(self._info.keys):
            d[key] = raw_data[idx]
        return d

    def _init_frameinfo(self, info: bytearray):
        fmt_unp = struct.unpack(BtSlaveInputStream._pres_frame_fmt, info)
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
        self._info = Frameinfo(framesize, lenchunks, chunk_fmt, data_keys)

    def _loop(self):
        try:
            # Init BT socket and loop
            # BUG in Win10 implementation, this will try to connect to previously paired
            # devices, even when not on or close enough, raising an OSError
            rf_port = 1
            self._sock.connect((self._mac, rf_port))
            self._running = True

            # Wait for a 112 B presentation frame
            fmt_len = 0
            fmt_frame = bytearray()
            while fmt_len < BtSlaveInputStream._pres_frame_size:
                fmt_frame += bytearray(self._sock.recv(BtSlaveInputStream._pres_frame_size))
                fmt_len = len(fmt_frame)

            # Parse presentation and notify the on connect callback
            self._init_frameinfo(fmt_frame)
            if self.on_connect:
                self.on_connect(self._mac, self._info)

            # Data reading loop based on frameinfo format
            while self._running:
                data_len = 0
                data = bytearray()
                while data_len < self._info.framesize:
                    data += bytearray(self._sock.recv(self._info.framesize))
                    data_len = len(data)
                for idx in range(0, self._info.framesize, self._info.lenchunks):
                    raw_data = struct.unpack(self._info.format, data[idx:idx + self._info.lenchunks])
                    # Msg received: Notify on message callback
                    if self.on_message:
                        self.on_message(self._mac, self._to_dict(raw_data))
            if self.on_disconnect:
                self.on_disconnect(self._mac, False)

        except bluetooth.btcommon.BluetoothError:
            if self._running and self.on_disconnect:
                self.on_disconnect(self._mac, True)
            else:
                raise bluetooth.BluetoothError(f"BT MAC {self._mac}: couldn't connect to the bluetooth interface")
        except struct.error:
            raise ConnectionError(f"BT MAC {self._mac}: error in decoding presentation frame!")
        finally:
            self._running = False
            self._sock.close()
