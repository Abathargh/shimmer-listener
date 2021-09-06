import shimmer_listener

import unittest


class TestDiscoveryIfc(unittest.TestCase):
    def tearDown(self):
        if shimmer_listener._op_mode is not None:
            shimmer_listener.bt_close()

    def test_bt_init_fail(self):
        shimmer_listener._running = True
        self.assertRaises(ValueError, shimmer_listener.bt_init, shimmer_listener.BtMode.SLAVE)
