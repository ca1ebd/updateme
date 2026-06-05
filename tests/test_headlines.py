"""Tests for modules.headlines pure functions."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.headlines import parse_rss, parse_newsapi


BBC_RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>BBC News</title>
    <link>https://www.bbc.co.uk/news</link>
    <description>BBC News RSS</description>
    <item>
      <title>Global leaders meet for climate summit</title>
      <link>https://www.bbc.co.uk/news/world-12345678</link>
    </item>
    <item>
      <title>Tech giant unveils new AI model</title>
      <link>https://www.bbc.co.uk/news/technology-87654321</link>
    </item>
    <item>
      <title>Markets rally after jobs report</title>
      <link>https://www.bbc.co.uk/news/business-11111111</link>
    </item>
  </channel>
</rss>"""


class TestParseRss(unittest.TestCase):
    def test_basic_parse(self):
        items = parse_rss(BBC_RSS_SAMPLE, 3)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["title"], "Global leaders meet for climate summit")
        self.assertEqual(items[0]["url"], "https://www.bbc.co.uk/news/world-12345678")

    def test_count_limit(self):
        items = parse_rss(BBC_RSS_SAMPLE, 2)
        self.assertEqual(len(items), 2)

    def test_count_larger_than_available(self):
        items = parse_rss(BBC_RSS_SAMPLE, 100)
        self.assertEqual(len(items), 3)

    def test_malformed_xml(self):
        items = parse_rss("<not valid xml at all >>>", 5)
        self.assertEqual(items, [])

    def test_empty_string(self):
        items = parse_rss("", 5)
        self.assertEqual(items, [])

    def test_no_items(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><title>Empty</title></channel></rss>"""
        items = parse_rss(xml, 5)
        self.assertEqual(items, [])

    def test_items_missing_link(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item><title>No link here</title></item>
            <item>
              <title>Has link</title>
              <link>https://example.com</link>
            </item>
          </channel>
        </rss>"""
        items = parse_rss(xml, 5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Has link")

    def test_items_with_default_namespace(self):
        # BBC feeds sometimes have a default namespace — we strip it
        xml = """<?xml version="1.0"?>
        <rss version="2.0" xmlns="http://purl.org/rss/1.0/">
          <channel>
            <item>
              <title>Namespaced item</title>
              <link>https://example.com/ns</link>
            </item>
          </channel>
        </rss>"""
        items = parse_rss(xml, 5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.com/ns")

    def test_count_zero(self):
        items = parse_rss(BBC_RSS_SAMPLE, 0)
        self.assertEqual(items, [])

    def test_dict_keys(self):
        items = parse_rss(BBC_RSS_SAMPLE, 1)
        self.assertIn("title", items[0])
        self.assertIn("url", items[0])


class TestParseNewsapi(unittest.TestCase):
    SAMPLE_DATA = {
        "status": "ok",
        "totalResults": 3,
        "articles": [
            {
                "title": "Fed holds rates steady",
                "url": "https://example.com/fed",
                "source": {"name": "Reuters"},
            },
            {
                "title": "Election results in",
                "url": "https://example.com/election",
                "source": {"name": "AP"},
            },
            {
                "title": "Space mission launches",
                "url": "https://example.com/space",
                "source": {"name": "NASA"},
            },
        ],
    }

    def test_basic_parse(self):
        items = parse_newsapi(self.SAMPLE_DATA, 3)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["title"], "Fed holds rates steady")
        self.assertEqual(items[0]["url"], "https://example.com/fed")

    def test_count_limit(self):
        items = parse_newsapi(self.SAMPLE_DATA, 2)
        self.assertEqual(len(items), 2)

    def test_empty_articles(self):
        items = parse_newsapi({"status": "ok", "articles": []}, 5)
        self.assertEqual(items, [])

    def test_missing_articles_key(self):
        items = parse_newsapi({}, 5)
        self.assertEqual(items, [])

    def test_none_title_skipped(self):
        data = {
            "articles": [
                {"title": None, "url": "https://example.com/1"},
                {"title": "Good title", "url": "https://example.com/2"},
            ]
        }
        items = parse_newsapi(data, 5)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Good title")

    def test_none_url_skipped(self):
        data = {
            "articles": [
                {"title": "Title", "url": None},
                {"title": "Other", "url": "https://example.com"},
            ]
        }
        items = parse_newsapi(data, 5)
        self.assertEqual(len(items), 1)

    def test_count_larger_than_available(self):
        items = parse_newsapi(self.SAMPLE_DATA, 100)
        self.assertEqual(len(items), 3)

    def test_dict_keys(self):
        items = parse_newsapi(self.SAMPLE_DATA, 1)
        self.assertIn("title", items[0])
        self.assertIn("url", items[0])

    def test_whitespace_stripped(self):
        data = {
            "articles": [
                {"title": "  Spaced title  ", "url": "  https://example.com  "},
            ]
        }
        items = parse_newsapi(data, 5)
        self.assertEqual(items[0]["title"], "Spaced title")
        self.assertEqual(items[0]["url"], "https://example.com")


if __name__ == "__main__":
    unittest.main()
