"""Harness-owned acceptance checks; never supplied as editable agent files."""
import runpy
import sys
import unittest
shipping = runpy.run_path(sys.argv[1])["shipping_pence"]
sys.argv = [sys.argv[0]]
class ShippingAcceptance(unittest.TestCase):
    def test_below(self): self.assertEqual(shipping(4999), 499)
    def test_at(self): self.assertEqual(shipping(5000), 0)
    def test_above(self): self.assertEqual(shipping(5001), 0)
    def test_zero(self): self.assertEqual(shipping(0), 499)
    def test_negative(self):
        with self.assertRaises(ValueError): shipping(-1)
unittest.main()
