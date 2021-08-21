"""
A small application that can be used to connect and start receiving 
data from a specific device by knowing its mac address in advance.

The application is blocking, stop it with ctrl+c

Usage:
    python bt_slave_stream.py **mac-address**
"""
from shimmer_listener import BtSlaveInputStream
import sys

def on_connect(mac, info):
    print(f"BT MAC {mac}: received presentation frame, {info}")

def on_disconnect(mac, lost):
    if lost:
        print(f"BT MAC {mac}: connection lost")
    else:
        print(f"BT MAC {mac}: disconnecting")

def on_message(mac, data):
    print(f"BT MAC {mac}: got {data}")
    
    
try:
    mac_address = sys.argv[1]
    ins = BtSlaveInputStream(mac_address)
    ins.on_connect = on_connect
    ins.on_disconnect = on_disconnect
    ins.on_message = on_message
    ins.loop_forever()
except IndexError:
    print("You must pass the mac-address of the mote to connect to as the first argument")
except KeyboardInterrupt:
    ins.stop()
    print("Bye")
