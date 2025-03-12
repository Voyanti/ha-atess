import unittest
import src.app as app
from modbus_client import SpoofClient
import logging
logging.disable(logging.CRITICAL)


class TestApp(unittest.TestCase):

    def setUp(self):
        def instantiate_spoof_clients(Options) -> list[SpoofClient]:
            return [SpoofClient()]

        self.app = app.App(
            modbus_client_setup=instantiate_spoof_clients,
            modbus_device_setup=app.instantiate_devices,
            options_rel_path="config.yaml"
        )

        self.app.setup()
        for s in self.app.devices:
            s.connect = lambda: None
        self.app.connect()

    def test_setup(self):
        self.assertEqual(1, 1)

    def test_one_loop(self):
        self.app.loop(loop_once=True)


if __name__ == "__main__":
    unittest.main()
