from shimmer_listener import bt_init, bt_listen, bt_close, BtMode
from threading import Lock
import argparse
import logging
import socket
import json
import sys


logging.basicConfig(level=logging.INFO)


def nodered_app():
    c_data_socket: socket.socket
    mutex = Lock()

    # The newline char is the data separator used in order for the tcp
    # node in node-red to understand that an instance of incoming data is arrived
    def forward(data: dict):
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
        bt_listen(process=forward)
    except KeyboardInterrupt:
        bt_close()
    finally:
        sys.exit(0)


def printer_app():
    def forward(data: dict):
        print(data)

    bt_init(mode=BtMode.MASTER)

    try:
        bt_listen(process=forward)
    except KeyboardInterrupt:
        bt_close()
    finally:
        sys.exit(0)


if __name__ == "__main__":
    printer_app()
