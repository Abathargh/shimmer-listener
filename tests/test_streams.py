import struct

import shimmer_listener
import bluetooth
import time

from unittest.mock import MagicMock
import unittest


data_frame = b"\xd0\x07\xd1\x07\xd2\x07\xd3\x07"
data_dict = {"accel_x": 2000, "accel_y": 2001, "accel_z": 2002, "batt": 2003}

bluetooth.BluetoothSocket.connect = MagicMock()


def custom_recv(frame_type):
    def recv(length):
        pres_frame = generate_frame(frame_type)
        if length == len(pres_frame):
            return pres_frame
        return data_frame
    return recv


def generate_frame(wrong: str) -> bytes:
    if wrong == "framesize":
        return struct.pack("BB10s100s", 0, 12, b"h", b"")
    if wrong == "lenchunk1":
        return struct.pack("BB10s100s", 10, 0, b"", b"")
    if wrong == "lenchunk2":
        return struct.pack("BB10s100s", 10, 12, b"hhhhhh", b"")
    if wrong == "lenchunk3":
        return struct.pack("BB10s100s", 10, 5, b"hh", b"")
    if wrong == "chunkfmt":
        return struct.pack("BB10s100s", 16, 4, b"hh", b"")

    ret = bytearray()
    ret += struct.pack("BB10s", 120, 8, b"hhhh")
    ret += struct.pack("10s", b"accel_x")
    ret += struct.pack("10s", b"accel_y")
    ret += struct.pack("10s", b"accel_z")
    ret += struct.pack("10s", b"batt")
    for _ in range(6):
        ret += struct.pack("10s", b"")
    return ret


class TestBtSlaveStream(unittest.TestCase):
    def setUp(self):
        self.mac = "mac"
        self.read = {"mac": "", "frame": "", "frameinfo_error": False, "message": {}}
        self.stream = shimmer_listener.BtSlaveInputStream(self.mac)
        bluetooth.BluetoothSocket.recv = MagicMock(side_effect=custom_recv("ok"))

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

    def test_wrong_framesize(self):
        def on_disconnect(_, lost):
            if lost:
                self.read["frameinfo_error"] = True
        self.stream.on_disconnect = on_disconnect
        bluetooth.BluetoothSocket.recv = MagicMock(side_effect=custom_recv("framesize"))
        self.stream.start()
        self.stream.stop()
        self.assertEqual(self.read["frameinfo_error"], True, "expected frameinfo_error to be set")

    def test_wrong_chunklen_zero(self):
        def on_disconnect(_, lost):
            if lost:
                self.read["frameinfo_error"] = True
        self.stream.on_disconnect = on_disconnect
        bluetooth.BluetoothSocket.recv = MagicMock(side_effect=custom_recv("lenchunk1"))
        self.stream.start()
        self.stream.stop()
        self.assertEqual(self.read["frameinfo_error"], True, "expected frameinfo_error to be set")

    def test_wrong_chunklen_greater(self):
        def on_disconnect(_, lost):
            if lost:
                self.read["frameinfo_error"] = True
        self.stream.on_disconnect = on_disconnect
        bluetooth.BluetoothSocket.recv = MagicMock(side_effect=custom_recv("lenchunk2"))
        self.stream.start()
        self.stream.stop()
        self.assertEqual(self.read["frameinfo_error"], True, "expected frameinfo_error to be set")

    def test_wrong_chunklen_multiple(self):
        def on_disconnect(_, lost):
            if lost:
                self.read["frameinfo_error"] = True
        self.stream.on_disconnect = on_disconnect
        bluetooth.BluetoothSocket.recv = MagicMock(side_effect=custom_recv("lenchunk3"))
        self.stream.start()
        self.stream.stop()
        self.assertEqual(self.read["frameinfo_error"], True, "expected frameinfo_error to be set")

    def test_wrong_chunkfmt(self):
        def on_disconnect(_, lost):
            if lost:
                self.read["frameinfo_error"] = True
        self.stream.on_disconnect = on_disconnect
        bluetooth.BluetoothSocket.recv = MagicMock(side_effect=custom_recv("chunkfmt"))
        self.stream.start()
        self.stream.stop()
        self.assertEqual(self.read["frameinfo_error"], True, "expected frameinfo_error to be set")

    def test_start(self):
        expected_frame = shimmer_listener.Frameinfo(120, 8, "hhhh", ["accel_x", "accel_y", "accel_z", "batt"])

        def on_connect(mac, info):
            self.read["mac"] = mac
            self.read["frame"] = info

        self.stream.on_connect = on_connect
        self.stream.start()
        time.sleep(1)
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
        time.sleep(1)
        self.assertEqual(self.read["mac"], self.mac, "expected passed mac, got another one")
        self.assertDictEqual(self.read["message"], data_dict, "expected passed msg")
