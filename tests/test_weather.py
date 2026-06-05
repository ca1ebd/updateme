"""Tests for modules.weather pure functions."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.weather import wmo_description, parse_forecast, parse_current


class TestWmoDescription(unittest.TestCase):
    def test_known_codes(self):
        self.assertEqual(wmo_description(0), "Clear sky")
        self.assertEqual(wmo_description(3), "Overcast")
        self.assertEqual(wmo_description(61), "Light rain")
        self.assertEqual(wmo_description(95), "Thunderstorm")
        self.assertEqual(wmo_description(99), "Thunderstorm + heavy hail")

    def test_unknown_code(self):
        self.assertEqual(wmo_description(999), "WMO 999")
        self.assertEqual(wmo_description(-1), "WMO -1")

    def test_fog(self):
        self.assertEqual(wmo_description(45), "Fog")

    def test_snow(self):
        self.assertEqual(wmo_description(73), "Snow")


class TestParseForecast(unittest.TestCase):
    SAMPLE_DAILY = {
        "time": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "weathercode": [0, 63, 71],
        "temperature_2m_max": [72.5, 65.0, 45.0],
        "temperature_2m_min": [55.0, 50.0, 30.0],
        "precipitation_probability_max": [5, 80, 90],
    }

    def test_basic_parse(self):
        days = parse_forecast(self.SAMPLE_DAILY)
        self.assertEqual(len(days), 3)
        self.assertEqual(days[0]["date"], "2025-01-01")
        self.assertEqual(days[0]["description"], "Clear sky")
        self.assertAlmostEqual(days[0]["hi"], 72.5)
        self.assertAlmostEqual(days[0]["lo"], 55.0)
        self.assertEqual(days[0]["rain"], 5)

    def test_second_day_rain(self):
        days = parse_forecast(self.SAMPLE_DAILY)
        self.assertEqual(days[1]["description"], "Rain")
        self.assertEqual(days[1]["rain"], 80)

    def test_third_day_snow(self):
        days = parse_forecast(self.SAMPLE_DAILY)
        self.assertEqual(days[2]["description"], "Light snow")

    def test_none_values_become_none(self):
        daily = {
            "time": ["2025-06-01"],
            "weathercode": [0],
            "temperature_2m_max": [None],
            "temperature_2m_min": [None],
            "precipitation_probability_max": [None],
        }
        days = parse_forecast(daily)
        self.assertEqual(len(days), 1)
        self.assertIsNone(days[0]["hi"])
        self.assertIsNone(days[0]["lo"])
        self.assertIsNone(days[0]["rain"])

    def test_empty_daily(self):
        days = parse_forecast({})
        self.assertEqual(days, [])

    def test_short_arrays(self):
        # weathercode array shorter than time array — should not raise
        daily = {
            "time": ["2025-01-01", "2025-01-02"],
            "weathercode": [0],
            "temperature_2m_max": [70.0, 72.0],
            "temperature_2m_min": [55.0, 56.0],
            "precipitation_probability_max": [10, 20],
        }
        days = parse_forecast(daily)
        self.assertEqual(len(days), 2)
        # Second day gets code=0 (index out of range → default)
        self.assertEqual(days[1]["description"], wmo_description(0))

    def test_rain_is_int(self):
        days = parse_forecast(self.SAMPLE_DAILY)
        for day in days:
            if day["rain"] is not None:
                self.assertIsInstance(day["rain"], int)


class TestParseCurrent(unittest.TestCase):
    SAMPLE_WTTR = {
        "current_condition": [
            {
                "weatherDesc": [{"value": "Partly cloudy"}],
                "temp_F": "78",
                "FeelsLikeF": "80",
                "windspeedMiles": "12",
                "humidity": "65",
            }
        ]
    }

    def test_basic_parse(self):
        result = parse_current(self.SAMPLE_WTTR)
        self.assertIsNotNone(result)
        self.assertEqual(result["desc"], "Partly cloudy")
        self.assertEqual(result["temp_f"], "78")
        self.assertEqual(result["feels_f"], "80")
        self.assertEqual(result["wind_mph"], "12")
        self.assertEqual(result["humidity"], "65")

    def test_empty_dict(self):
        self.assertIsNone(parse_current({}))

    def test_empty_current_condition_list(self):
        self.assertIsNone(parse_current({"current_condition": []}))

    def test_missing_weather_desc(self):
        data = {
            "current_condition": [
                {
                    "weatherDesc": [{}],
                    "temp_F": "70",
                    "FeelsLikeF": "68",
                    "windspeedMiles": "5",
                    "humidity": "50",
                }
            ]
        }
        result = parse_current(data)
        # desc will be empty string — but temp_f is set, so result may or may not be None
        # Implementation returns None only if both desc and temp_f are falsy
        self.assertIsNotNone(result)
        self.assertEqual(result["desc"], "")

    def test_none_current_condition(self):
        data = {"current_condition": None}
        result = parse_current(data)
        self.assertIsNone(result)

    def test_malformed_weather_desc(self):
        data = {
            "current_condition": [
                {
                    "weatherDesc": "not a list",
                    "temp_F": "60",
                }
            ]
        }
        # Should not raise — returns None gracefully
        result = parse_current(data)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
