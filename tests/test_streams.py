import shimmer_listener
import bluetooth
import time

from unittest.mock import MagicMock
import unittest

pres_frame = b"x\x08hhhh\x00\x00\x00\x00\x00\x00accel_x\x00\x00\x00accel_y\x00\x00\x00accel_z\x00\x00\x00batt\x00\x00" \
             b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
             b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
             b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

data_frame = b"\xd0\x07\xd1\x07\xd2\x07\xd3\x07"
data_dict = {"accel_x": 2000, "accel_y": 2001, "accel_z": 2002, "batt": 2003}


def recv(length):
    if length == len(pres_frame):
        return pres_frame
    return data_frame


bluetooth.BluetoothSocket.connect = MagicMock()
bluetooth.BluetoothSocket.recv = MagicMock(side_effect=recv)


class TestBtSlaveStream(unittest.TestCase):
    def setUp(self):
        self.mac = "mac"
        self.read = {}
        self.stream = shimmer_listener.BtSlaveInputStream(self.mac)

    def tearDown(self):
        if self.stream.open:
            self.stream.stop()

    def test_is_closed_startup(self):
        self.assertEqual(self.stream.open, False, "stream open property returns True before after starting it")

    def test_is_closed_end(self):
        self.stream.start()
        self.stream.stop()
        self.assertEqual(self.stream.open, False, "stream open property returns True after closing it")

    def test_is_open(self):
        self.stream.start()
        self.assertEqual(self.stream.open, True, "stream open property returns False after starting it")

    def test_start(self):
        expected_frame = shimmer_listener.Frameinfo(120, 8, "hhhh", ["accel_x", "accel_y", "accel_z", "batt"])

        def on_connect(mac, info):
            self.read["mac"] = mac
            self.read["frame"] = info

        self.stream.on_connect = on_connect
        self.stream.start()
        self.assertEqual(self.read["mac"], self.mac, "expected passed mac, got another one")
        self.assertEqual(self.read["frame"], expected_frame, "expected passed presentation frame, got another one")

    def test_stop(self):
        def on_disconnect(mac, lost):
            self.read["mac"] = mac
            self.read["lost"] = lost

        self.stream.on_disconnect = on_disconnect
        self.stream.start()
        self.stream.stop()
        time.sleep(0.05)
        self.assertEqual(self.read["mac"], self.mac, "expected passed mac, got another one")
        self.assertEqual(self.read["lost"], False, "expected stream closed, not lost")

    def test_incoming_msg(self):
        def on_message(mac, message):
            self.read["mac"] = mac
            self.read["message"] = message

        self.stream.on_message = on_message
        self.stream.start()
        self.assertEqual(self.read["mac"], self.mac, "expected passed mac, got another one")
        self.assertDictEqual(self.read["message"], data_dict, "expected passed msg")
