import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('board_identity', ROOT / 'board_identity.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'chosen').mkdir()
        self.put('model', b'Raspberry Pi 5 Model B Rev 1.0\0')
        self.put('serial-number', b'1234567890abcdef\0')
        self.put('chosen/rpi-serial64', b'1234567890ABCDEF\0')

    def put(self, name, value):
        (self.root / name).write_bytes(value)

    def test_valid_matching_serials(self):
        self.assertEqual(identity.read_identity(self.root)['serial'], '1234567890abcdef')

    def test_missing_property_stops(self):
        (self.root / 'chosen/rpi-serial64').unlink()
        with self.assertRaises(ValueError):
            identity.read_identity(self.root)

    def test_mismatch_stops(self):
        self.put('chosen/rpi-serial64', b'0123456789abcdef\0')
        with self.assertRaises(ValueError):
            identity.read_identity(self.root)

    def test_bad_serial_stops(self):
        for serial in (b'0000000000000000', b'broken', b'12345678\0junk', b'\xff'):
            self.put('serial-number', serial)
            with self.subTest(serial=serial), self.assertRaises(ValueError):
                identity.read_identity(self.root)

    def test_wrong_model_stops(self):
        self.put('model', b'Raspberry Pi 4 Model B Rev 1.0\0')
        with self.assertRaises(ValueError):
            identity.read_identity(self.root)

    def test_oversized_property_stops(self):
        self.put('model', b'x' * 257)
        with self.assertRaises(ValueError):
            identity.read_identity(self.root)


if __name__ == '__main__':
    unittest.main()
