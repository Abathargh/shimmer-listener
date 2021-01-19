"""
This library allows you to connect to a Shimmer2 mote via Bluetooth both in Master and Slave
mode, interacting with the applications on the mote.
"""

from ._streams import BtSlaveInputStream, BtMasterInputStream, frameinfo, close_streams
from ._slave import _slave_init, _slave_listen, _slave_close
from ._master import _master_listen, _master_close

from typing import Optional, Callable, Any, Dict, List
import enum


__all__ = ["bt_init", "bt_listen", "bt_close", "frameinfo", "BtMode", "BtSlaveInputStream"]


class BtMode(enum.Enum):
    """
    Used to represent the mode in which the program is acting towards the shimmer devices
    """
    MASTER = 0
    SLAVE = 1

    @property
    def index(self):
        return self.value


listen: List[Callable] = [_master_listen, _slave_listen]
close: List[Callable] = [_master_close, _slave_close]
_op_mode: Optional[BtMode] = None
_running: bool = False


def bt_init(mode: BtMode) -> None:
    """
    Initializes the bluetooth server socket interface.
    Call this at the beginning of your program.
    :param mode: One between BtMode.MASTER or BtMode.SLAVE
    :return: None
    """
    global _op_mode, _running
    if _running:
        raise ValueError("Trying to initialize an already started interface")
    if mode == BtMode.SLAVE:
        _slave_init()
    _op_mode = mode
    _running = True


def bt_listen(connect_handle: Optional[Callable[[str, frameinfo], None]] = None,
              message_handle: Optional[Callable[[str, Dict[str, Any]], None]] = None,
              disconnect_handle: Optional[Callable[[str, bool], None]] = None) -> None:
    """
    Starts the listen loop
    :return: None
    """
    global _op_mode
    if _op_mode is None or not _running:
        raise ValueError("Listen operation on non initialized interface")
    listen[_op_mode.index](connect_handle, message_handle, disconnect_handle)


def bt_close() -> None:
    """
    Gracefully stop any open connection
    :return: None
    """
    global _op_mode, _running
    if _op_mode is None:
        raise ValueError("Trying to close a non initialized interface")
    close[_op_mode.index]()
    close_streams()

    _op_mode = None
    _running = False
