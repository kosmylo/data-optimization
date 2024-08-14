import unittest
import pandas as pd
from utils import schedule_battery, compute_soc_schedule

class TestScheduler(unittest.TestCase):

    def setUp(self):
        # Set up common parameters for tests
        raw_prices = dict(
            production=[7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6],
            consumption=[8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7],
        )

        self.prices = pd.DataFrame(raw_prices, index=pd.date_range("2000-01-01T00:00+01", periods=len(raw_prices["consumption"]), freq="1H", inclusive="left"))

    def test_normal_operation(self):
        # Test with standard parameters
        costs, power_schedule = schedule_battery(
            prices=self.prices,
            soc_start=20.0,
            soc_max=90.0,
            soc_min=10.0,
            soc_target=90.0,
            power_capacity=10.0,
            storage_capacity=100.0,
            conversion_efficiency=1.0,
            top_up=False
        )
        soc_schedule = compute_soc_schedule(power_schedule, soc_start=20.0, conversion_efficiency=1.0)

        self.assertEqual(len(power_schedule), len(self.prices))
        self.assertTrue(len(power_schedule) > 0)
        self.assertTrue(len(soc_schedule) > 0)
        self.assertAlmostEqual(soc_schedule[-1], 90.0, delta=1e-2)

    def test_top_up_operation(self):
        # Test with top_up set to true
        costs, power_schedule = schedule_battery(
            prices=self.prices,
            soc_start=20.0,
            soc_max=90.0,
            soc_min=10.0,
            soc_target=90.0,
            power_capacity=10.0,
            storage_capacity=100.0,
            conversion_efficiency=1.0,
            top_up=True
        )
        soc_schedule = compute_soc_schedule(power_schedule, soc_start=20.0, conversion_efficiency=1.0)

        self.assertTrue(len(power_schedule) > 0)
        self.assertTrue(len(soc_schedule) > 0)
        # Check that the final SOC reaches the storage capacity
        self.assertAlmostEqual(soc_schedule[-1], 100.0, delta=1e-2)

    def test_infeasible_soc_target(self):
        # Test for infeasible SOC target (e.g., target higher than storage capacity)
        with self.assertRaises(ValueError):
            schedule_battery(
                prices=self.prices,
                soc_start=20,
                soc_max=90,
                soc_min=10,
                soc_target=110,  # Infeasible, exceeds storage capacity
                power_capacity=10,
                storage_capacity=100,
                conversion_efficiency=1.0,
                top_up=False
            )

    def test_infeasible_power_capacity(self):
        # Test for infeasible power capacity (too low to meet SOC target)
        with self.assertRaises(ValueError):
            schedule_battery(
                prices=self.prices,
                soc_start=20,
                soc_max=90,
                soc_min=10,
                soc_target=90,
                power_capacity=1,  # Too low to achieve target in time
                storage_capacity=100,
                conversion_efficiency=1.0,
                top_up=False
            )

    def test_invalid_soc_bounds(self):
        # Test with invalid SOC bounds (min >= max)
        with self.assertRaises(ValueError):
            schedule_battery(
                prices=self.prices,
                soc_start=20,
                soc_max=10,  # Invalid, max < start
                soc_min=90,
                soc_target=50,
                power_capacity=10,
                storage_capacity=100,
                conversion_efficiency=1.0,
                top_up=False
            )

    def test_negative_power_capacity(self):
        # Test with negative power capacity
        with self.assertRaises(ValueError):
            schedule_battery(
                prices=self.prices,
                soc_start=20,
                soc_max=90,
                soc_min=10,
                soc_target=50,
                power_capacity=-10,  # Invalid, negative capacity
                storage_capacity=100,
                conversion_efficiency=1.0,
                top_up=False
            )

    def test_insufficient_storage_capacity(self):
        # Test with a storage capacity that is insufficient for the soc_target
        with self.assertRaises(ValueError):
            schedule_battery(
                prices=self.prices,
                soc_start=20,
                soc_max=90,
                soc_min=10,
                soc_target=95,  # Too high for given storage capacity
                power_capacity=10,
                storage_capacity=90,  # Insufficient storage capacity
                conversion_efficiency=1.0,
                top_up=True
            )

if __name__ == '__main__':
    unittest.main()