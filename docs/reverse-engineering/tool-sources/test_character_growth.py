import unittest
from character_growth import tier, level_up


class GrowthTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual([tier(n) for n in [24,25,34,35,44,45]], [1,2,2,3,3,4])

    def test_rounding_and_level_cap(self):
        values, level = level_up([10]*7, [24,25,35,45,45], [2]*7, 49, 5)
        self.assertEqual(level, 50)
        self.assertEqual(values, [11,12,12,13,13,12,12])

    def test_attribute_caps(self):
        values, level = level_up([254]*5+[499,249], [45]*5, [4]*7, 48, 2)
        self.assertEqual(values, [255]*5+[500,250])


if __name__ == '__main__':
    unittest.main()
