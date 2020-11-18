from shimmer_listener import bt_init, bt_listen, bt_close, BtMode
from threading import Lock
import argparse
import logging
import socket
import json

logging.basicConfig(level=logging.INFO)

description = "Forwards data to a specific socket port on the machine identified by the specified address. " \
              "Used along with a nodered instance where a tcp node acts as the data source."
port_help = "The socket port to use to forward the shimmer data"
host_help = "The server address that is listening at the given port; defaults to 'localhost'"

parser = argparse.ArgumentParser(description)
parser.add_argument("--port", "-p", type=int, required=True, help=port_help)
parser.add_argument("--server", "-s", type=str, help=host_help, default="localhost")

c_data_socket: socket.socket
mutex = Lock()


def socket_init(host: str, port: int) -> None:
    global c_data_socket
    c_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c_data_socket.connect((host, port))


# The newline char is the data separator used in order for the tcp
# node in ndoe-red to understand that an instance of incoming data is arrived
def forward(data: dict):
    j_data = json.dumps(data)
    with mutex:
        c_data_socket.send((j_data + "\n").encode())


def main():
    args = parser.parse_args()
    bt_init(mode=BtMode.MASTER, node_app="simple_accel")
    socket_init(host=args.server, port=args.port)

    try:
        bt_listen(process=forward)
    except KeyboardInterrupt:
        bt_close()


if __name__ == "__main__":
    main()
