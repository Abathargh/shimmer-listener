"""
Loosely based on the bluetoothMasterTwe
est.py app from https://github.com/ShimmerResearch/tinyos-shimmer

We acquire data from the accelerometer and from the gyroscope modules on the mote, format them, and process
them via a process function. This approach can be used both for data to be locally transformed or for the data
to be forwarded to other apps (e.g. nodered)
"""

from typing import Callable, Optional, Dict
import enum

from ._slave import _slave_init, _slave_listen, _slave_close
from ._master import _master_listen, _master_close
from ._streams import close_streams

__all__ = ["bt_init", "bt_listen", "bt_close", "BtMode"]


listen = [_master_listen, _slave_listen]
close = [_master_close, _slave_close]


class BtMode(enum.Enum):
    """
    Used to represent the mode in which the program is acting towards the shimmer devices
    """
    MASTER = 0
    SLAVE = 1

    @property
    def index(self):
        return self.value


_op_mode: Optional[BtMode] = None


def bt_init(mode: BtMode) -> None:
    """
    Initializes the bluetooth server socket interface.
    Call this at the beginning of your program.
    :param mode: Slave or Master mode
    :return: None
    """
    global _op_mode
    if _op_mode is not None:
        raise ValueError("Trying to initialize an already started interface")
    _op_mode = mode

    if _op_mode == BtMode.SLAVE:
        _slave_init()


def bt_listen(process: Callable[[Dict], None]) -> None:
    """
    Starts the listen loop
    :param process: a void function taking in a DataTuple
    :return: None
    """
    global _op_mode
    if _op_mode is None:
        raise ValueError("Listen operation on non initialized interface")
    listen[_op_mode.index](process)


def bt_close() -> None:
    """
    Gracefully stop any open connection
    :return: None
    """
    global _op_mode
    if _op_mode is None:
        raise ValueError("Trying to close a non initialized interface")
    close[_op_mode.index]()
    close_streams()
