import unittest

from src.atess_inverter import AtessInverter
from src.atess_registers_v2 import atess_param_registry
from src.enums import DataType, HAEntityType


class TestWriteEncoding(unittest.TestCase):
    def test_fractional_multiplier_rounds_not_truncates(self):
        """0.999 / 0.001 lands on 998.9999... in float; truncating writes 998."""
        self.assertEqual(AtessInverter._encoded(None, 0.999 / 0.001, DataType.U16), [999])
        self.assertEqual(AtessInverter._encoded(None, 0.95 / 0.001, DataType.U16), [950])
        self.assertEqual(AtessInverter._encoded(None, 12.3 / 0.1, DataType.U16), [123])

    def test_fractional_number_registers_declare_a_step(self):
        """HA number entities default to step=1, which makes a 0-1 register useless."""
        for name, param in atess_param_registry.build_map("HPS", True).items():
            if param.get("ha_entity_type") is not HAEntityType.NUMBER:
                continue
            if param["multiplier"] == 1:
                continue
            span = param.get("max", 0) - param.get("min", 0)
            if span > 1:
                continue  # integer steps still resolve a wide range acceptably
            self.assertIn("step", param, f"{name} needs an explicit step")


if __name__ == "__main__":
    unittest.main()
