"""
An example of BT Master app connecting with one ore more shimmer devices, acting as BT slaves.
This example contains each basic functionality of the library master interface.
"""
from shimmer_listener import bt_init, bt_listen, bt_close, BtMode


def main():
    def on_connect(mac, info):
        print(f"BT MAC {mac}: received presentation frame, {info} ")

    def on_disconnect(mac, lost):
        if lost:
            print(f"BT MAC {mac}: connection lost")
        else:
            print(f"BT MAC {mac}: disconnecting")

    def on_message(mac, data):
        print(f"BT MAC {mac}: got {data}")

    bt_init(mode=BtMode.MASTER)

    try:
        bt_listen(connect_handle=on_connect, message_handle=on_message,
                  disconnect_handle=on_disconnect)
    except KeyboardInterrupt:
        bt_close()


if __name__ == "__main__":
    main()
