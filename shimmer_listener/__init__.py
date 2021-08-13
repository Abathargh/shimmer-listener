"""
## shimmer-listener

This library allows you to connect to a Shimmer2/2r mote via Bluetooth both in Master and Slave
mode, interacting with the applications on the mote.

When communicating with a Shimmer mote using an app made with this library as the Bluetooth Master,
you have to implement the presentation protocol inside of the Shimmer nesC application. This protocol is a way
to inform the Bt Master about the data format used when sending messages.

## Presentation protocol

The protocol is implemented by sending a simple struct via Bluetooth as the very first message after successfully
establishing a connection with the Bt Master. Its format is the following:

```c
typedef char key_string[MAX_STR_LEN];

typedef struct {
    uint8_t framesize;
    uint8_t chunklen;
    char format[MAX_FMT_LEN];
    key_string keys[MAX_KEY_NUM];
} frameinfo;
```

The presentation frame is automatically interpreted from the BtStream, so you don't have to do anything from this side
of the communication.


## Callbacks


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

from ._streams import BtStream, BtSlaveInputStream, BtMasterInputStream, Frameinfo
from ._slave import _slave_init, _slave_listen, _slave_close
from ._master import _master_listen, _master_close

from typing import Optional, Callable, Any, Dict, List
import enum


__all__ = ["bt_init", "bt_listen", "bt_close", "Frameinfo", "BtMode", "BtStream",
           "BtMasterInputStream", "BtSlaveInputStream"]


class BtMode(enum.Enum):
    """
    Enum used to set the mode in which the library is acting towards the shimmer devices.
    """

    MASTER = 0
    SLAVE = 1

    @property
    def index(self):
        """
        Returns a numerical representation of the enum values, where MASTER = 0, SLAVE = 1.
        """
        return self.value


listen: List[Callable] = [_master_listen, _slave_listen]
close: List[Callable] = [_master_close, _slave_close]
_op_mode: Optional[BtMode] = None
_running: bool = False


def bt_init(mode: BtMode) -> None:
    """
    Initializes the bluetooth server socket interface.
    Call this at the beginning of your program.
    """
    global _op_mode, _running
    if _running:
        raise ValueError("Trying to initialize an already started interface")
    if mode == BtMode.SLAVE:
        _slave_init()
    _op_mode = mode
    _running = True


def bt_listen(connect_handle: Optional[Callable[[str, Frameinfo], None]] = None,
              message_handle: Optional[Callable[[str, Dict[str, Any]], None]] = None,
              disconnect_handle: Optional[Callable[[str, bool], None]] = None) -> None:
    """
    Starts the listen loop, attaching the passed handlers as event callbacks to each
    stream that is started.
    """
    global _op_mode
    if _op_mode is None or not _running:
        raise ValueError("Listen operation on non initialized interface")
    listen[_op_mode.index](connect_handle, message_handle, disconnect_handle)


def bt_close() -> None:
    """
    Gracefully stops any open connection.
    """
    global _op_mode, _running
    if _op_mode is None:
        raise ValueError("Trying to close a non initialized interface")
    close[_op_mode.index]()

    _op_mode = None
    _running = False
