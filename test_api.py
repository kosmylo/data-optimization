import unittest
from flask import Flask
from battery_schedule import app 

class TestScheduleAPI(unittest.TestCase):

    def setUp(self):
        # Set up Flask test client
        self.client = app.test_client()
        self.client.testing = True

    def test_get_schedule(self):
        # Test the basic schedule endpoint
        response = self.client.get('/schedule?top-up=false')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('costs', data)
        self.assertIn('power_schedule', data)
        self.assertIn('soc_schedule', data)

    def test_get_schedule_top_up(self):
        # Test the schedule endpoint with top-up
        response = self.client.get('/schedule?top-up=true')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('costs', data)
        self.assertIn('power_schedule', data)
        self.assertIn('soc_schedule', data)

    def test_infeasible_soc_target(self):
        # Mock a case where the SOC target is infeasible
        response = self.client.get('/schedule?top-up=false&soc-target=150')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_invalid_parameters(self):
        # Simulate a scenario with invalid parameters
        response = self.client.get('/schedule?top-up=false&soc-max=10&soc-min=90')
        data = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()