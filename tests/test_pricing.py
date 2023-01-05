import unittest
from slipstream.trading.model import Price, PriceLike, PriceRange


class PriceClassTests(unittest.TestCase):
    def test_price_ops(self):
        p1 = Price(1.0)
        p2 = Price(2.0)
        ps_add = p1 + p2
        self.assertEqual(ps_add, 3.0)
        self.assertTrue(isinstance(ps_add, Price))

        ps_add = p1 + 3.0
        self.assertEqual(ps_add, 4.0)
        self.assertTrue(isinstance(ps_add, Price))

        ps_sub = p1 - p2
        self.assertEqual(ps_sub, -1.0)
        self.assertTrue(isinstance(ps_sub, Price))

        ps_mul = p2 * p2
        self.assertEqual(ps_mul, 4.0)
        self.assertTrue(isinstance(ps_mul, Price))

        ps_mul = p2 * 3.0
        self.assertEqual(ps_mul, 6.0)
        self.assertTrue(isinstance(ps_mul, Price))

        ps_div = p2 / 10.0
        self.assertEqual(ps_div, 0.2)
        self.assertTrue(isinstance(ps_div, Price))

        ps_div = 10.0 / p2
        self.assertEqual(ps_div, 5.0)
        self.assertTrue(isinstance(ps_div, Price))

    def test_price_comparisons(self):
        self.assertTrue(Price(2.0) > 1.0)
        self.assertTrue(2.0 > Price(1.0))
        self.assertTrue(Price(2.0) >= 1.0)
        self.assertTrue(2.0 >= Price(1.0))
        self.assertTrue(Price(1.0) < 2.0)
        self.assertTrue(1.0 < Price(2.0))
        self.assertTrue(Price(1.0) <= 2.0)
        self.assertTrue(1.0 <= Price(2.0))
        self.assertFalse(Price(1.0) == 2.0)
        self.assertFalse(1.0 == Price(2.0))
        self.assertTrue(Price(1.0) != 2.0)
        self.assertTrue(1.0 != Price(2.0))
        self.assertEqual(max(0.0, 1.0, Price(2.0)), 2.0)
        self.assertEqual(min(100.0, 10.0, Price(20)), Price(10.0))

    def test_initializations(self):
        p1 = Price(123.0)
        p2 = Price(p1)
        self.assertEqual(p2, 123.0)

        with self.assertRaises(expected_exception=ValueError) as context:
            p3 = Price("Price cannot process string")
        print(f"Caught during test: \"{context.exception}\"")


if __name__ == '__main__':
    unittest.main()
