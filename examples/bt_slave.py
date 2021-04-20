"""
An example app to interact with the BluetoothMasterTest example in the tinyos.
Loosely based on the bluetoothMasterTest.py app from https://github.com/ShimmerResearch/tinyos-shimmer.
"""
from shimmer_listener import bt_init, bt_listen, bt_close, BtMode
import logging

logging.basicConfig(level=logging.INFO)


def main():
    def on_message(mac, data):
        logging.info(f"BT MAC {mac}: got {data}")

    bt_init(BtMode.SLAVE)

    try:
        bt_listen(message_handle=on_message)
    except KeyboardInterrupt:
        bt_close()


if __name__ == "__main__":
    main()
