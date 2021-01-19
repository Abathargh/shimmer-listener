from shimmer_listener import bt_init, bt_listen, bt_close, BtMode
from threading import Lock
import bluetooth
import argparse
import logging
import socket
import json


logging.basicConfig(level=logging.INFO)


def btmastertest_app():
    """
    Loosely based on the bluetoothMasterTest.py app from https://github.com/ShimmerResearch/tinyos-shimmer
    """

    def on_message(mac, data):
        logging.info(f"BT MAC {mac}: got {data}")

    bt_init(BtMode.SLAVE)

    try:
        bt_listen(message_handle=on_message)
    except KeyboardInterrupt:
        bt_close()


def nodered_app():
    c_data_socket: socket.socket
    mutex = Lock()

    # The newline char is the data separator used in order for the tcp
    # node in node-red to understand that an instance of incoming data is arrived
    def on_message(mac, data):
        j_data = json.dumps(data)
        with mutex:
            c_data_socket.send((j_data + "\n").encode())

    description = "Forwards data to a specific socket port on the machine identified by the specified address. " \
                  "Used along with a nodered instance where a tcp node acts as the data source."
    port_help = "The socket port to use to forward the shimmer data"
    host_help = "The server address that is listening at the given port; defaults to 'localhost'"

    parser = argparse.ArgumentParser(description)
    parser.add_argument("--port", "-p", type=int, required=True, help=port_help)
    parser.add_argument("--server", "-s", type=str, help=host_help, default="localhost")

    args = parser.parse_args()
    bt_init(mode=BtMode.MASTER)
    c_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c_data_socket.connect((args.server, args.port))

    try:
        bt_listen(message_handle=on_message)
    except bluetooth.btcommon.BluetoothError as be:
        logging.error(be)
        bt_close()
    except KeyboardInterrupt:
        bt_close()


def printer_app():
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


if __name__ == "__main__":
    printer_app()
