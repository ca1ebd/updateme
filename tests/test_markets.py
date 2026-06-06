"""Tests for modules.markets pure functions."""
import sys
import os
import unittest

# Make sure parent dir is on path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.markets import pct_change, fmt_pct, parse_ticker_response


class TestPctChange(unittest.TestCase):
    def test_positive_change(self):
        closes = [100.0, 105.0, 110.0]
        # n=1: (110 - 105) / 105 * 100
        result = pct_change(closes, 1)
        self.assertAlmostEqual(result, 4.761904, places=4)

    def test_negative_change(self):
        closes = [100.0, 90.0]
        result = pct_change(closes, 1)
        self.assertAlmostEqual(result, -10.0)

    def test_zero_change(self):
        closes = [50.0, 50.0]
        result = pct_change(closes, 1)
        self.assertAlmostEqual(result, 0.0)

    def test_insufficient_data_exact(self):
        # n == len(closes) → not enough
        closes = [100.0, 110.0]
        self.assertIsNone(pct_change(closes, 2))

    def test_insufficient_data_empty(self):
        self.assertIsNone(pct_change([], 5))

    def test_zero_base_price(self):
        closes = [0.0, 100.0]
        self.assertIsNone(pct_change(closes, 1))

    def test_longer_history(self):
        # Build 10-element list: 100 → 200 (last)
        closes = [100.0] * 9 + [200.0]
        result = pct_change(closes, 9)
        self.assertAlmostEqual(result, 100.0)

    def test_single_element(self):
        self.assertIsNone(pct_change([100.0], 1))

    def test_n_zero_always_zero(self):
        # n=0: (closes[-1] - closes[-1]) / closes[-1] == 0
        closes = [80.0, 120.0]
        result = pct_change(closes, 0)
        self.assertAlmostEqual(result, 0.0)


class TestFmtPct(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(fmt_pct(1.234), "+1.23%")

    def test_negative(self):
        self.assertEqual(fmt_pct(-5.678), "-5.68%")

    def test_zero(self):
        self.assertEqual(fmt_pct(0.0), "+0.00%")

    def test_none(self):
        self.assertEqual(fmt_pct(None), "N/A")

    def test_large_positive(self):
        self.assertEqual(fmt_pct(123.456), "+123.46%")


class TestParseTickerResponse(unittest.TestCase):
    SAMPLE_DATA = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "symbol": "AAPL",
                        "shortName": "Apple Inc.",
                        "regularMarketPrice": 189.50,
                    },
                    "indicators": {
                        "quote": [
                            {
                                "close": [180.0, None, 182.0, True, 185.0, 189.50]
                            }
                        ]
                    },
                }
            ]
        }
    }

    def test_basic_parse(self):
        result = parse_ticker_response(self.SAMPLE_DATA, "AAPL")
        self.assertEqual(result["ticker"], "AAPL")
        self.assertEqual(result["name"], "Apple Inc.")
        self.assertAlmostEqual(result["price"], 189.50)

    def test_filters_none_and_bool(self):
        result = parse_ticker_response(self.SAMPLE_DATA, "AAPL")
        # None and True should be filtered out
        for c in result["closes"]:
            self.assertIsInstance(c, float)
        self.assertEqual(result["closes"], [180.0, 182.0, 185.0, 189.50])

    def test_fallback_name_to_ticker(self):
        data = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "XYZ"},
                        "indicators": {"quote": [{"close": [10.0]}]},
                    }
                ]
            }
        }
        result = parse_ticker_response(data, "XYZ")
        self.assertEqual(result["name"], "XYZ")

    def test_malformed_data_returns_fallback(self):
        result = parse_ticker_response({}, "FAIL")
        self.assertEqual(result["ticker"], "FAIL")
        self.assertEqual(result["closes"], [])
        self.assertIsNone(result["price"])

    def test_all_closes_are_none(self):
        data = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "NULL", "regularMarketPrice": 5.0},
                        "indicators": {"quote": [{"close": [None, None, None]}]},
                    }
                ]
            }
        }
        result = parse_ticker_response(data, "NULL")
        self.assertEqual(result["closes"], [])
        self.assertAlmostEqual(result["price"], 5.0)

    def test_name_truncated_to_25_chars(self):
        long_name = "A" * 30
        data = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "T", "shortName": long_name, "regularMarketPrice": 1.0},
                        "indicators": {"quote": [{"close": [1.0]}]},
                    }
                ]
            }
        }
        result = parse_ticker_response(data, "T")
        self.assertLessEqual(len(result["name"]), 25)

    def test_missing_regular_market_price_uses_last_close(self):
        data = {
            "chart": {
                "result": [
                    {
                        "meta": {"symbol": "X"},
                        "indicators": {"quote": [{"close": [10.0, 20.0, 30.0]}]},
                    }
                ]
            }
        }
        result = parse_ticker_response(data, "X")
        self.assertAlmostEqual(result["price"], 30.0)


if __name__ == "__main__":
    unittest.main()
