import unittest
from pathlib import Path
from eex_cursor import Cursor


class CursorTests(unittest.TestCase):
    def test_original_opening_string(self):
        cursor = Cursor(Path('R_00.eex').read_bytes(), 0x14)
        self.assertEqual(cursor.parameter(5).hex(),
                         'c2d2cac0d6aebce9d0dba3acd6ce cac0d6aec4dcb3bca1a3'.replace(' ', ''))
        self.assertEqual(cursor.pos, 0x2f)

    def test_numeric_and_mismatch_cursor(self):
        cursor = Cursor(bytes.fromhex('04007856341202000a000300'))
        self.assertEqual(cursor.parameter(4), 0x12345678)
        self.assertEqual(cursor.parameter(2), 10)
        self.assertEqual(cursor.parameter(5), 0x80000000)
        self.assertEqual(cursor.pos, 12)

    def test_truncation(self):
        with self.assertRaises(ValueError):
            Cursor(b'\x04\x00\x01').parameter(4)
        with self.assertRaises(ValueError):
            Cursor(b'\x05\x00text').parameter(5)


if __name__ == '__main__':
    unittest.main()
