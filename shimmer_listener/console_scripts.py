from shimmer_listener import bt_init, bt_listen, bt_close, BtMode
import bluetooth
import logging


logging.basicConfig(level=logging.INFO)


def btmastertest_app():
    """
    An example app to interact with the BluetoothMasterTest example in the tinyos.
    Loosely based on the bluetoothMasterTest.py app from https://github.com/ShimmerResearch/tinyos-shimmer.
    """

    def on_message(mac, data):
        logging.info(f"BT MAC {mac}: got {data}")

    bt_init(BtMode.SLAVE)

    try:
        bt_listen(message_handle=on_message)
    except KeyboardInterrupt:
        bt_close()


def printer_app():
    """
    Simple app that logs every action using user-defined callbacks.
    """
    def on_connect(mac, info):
        logging.info(f"BT MAC {mac}: received presentation frame, {info} ")

    def on_disconnect(mac, lost):
        if lost:
            logging.error(f"BT MAC {mac}: connection lost")
        else:
            logging.info(f"BT MAC {mac}: disconnecting")

    def on_message(mac, data):
        logging.info(f"BT MAC {mac}: got {data}")

    bt_init(mode=BtMode.MASTER)

    try:
        bt_listen(connect_handle=on_connect, message_handle=on_message,
                  disconnect_handle=on_disconnect)
    except bluetooth.btcommon.BluetoothError as be:
        logging.error(be)
        bt_close()
    except KeyboardInterrupt:
        bt_close()
