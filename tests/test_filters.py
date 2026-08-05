import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.filters import filter_postings, is_fall_2026, is_internship, tag_posting


class TestInternshipMatching(unittest.TestCase):
    def test_matches_internship_variants(self):
        positives = [
            "Summer Internship",
            "Software Intern",
            "Interns wanted",
            "Co-op Program",
            "Coop position",
            "Co-Ops available",
        ]
        for text in positives:
            with self.subTest(text=text):
                self.assertTrue(is_internship(text))

    def test_does_not_match_internal_or_international(self):
        negatives = [
            "Internal Audit Analyst",
            "International Tax Associate",
            "Head of Internal Communications",
            "International Business Manager",
        ]
        for text in negatives:
            with self.subTest(text=text):
                self.assertFalse(is_internship(text))


class TestFall2026Tagging(unittest.TestCase):
    def test_fall_2026_either_word_order(self):
        self.assertTrue(is_fall_2026("Fall 2026 Finance Internship"))
        self.assertTrue(is_fall_2026("2026 Fall Accounting Intern"))
        self.assertTrue(is_fall_2026("Autumn 2026 Software Intern"))
        self.assertTrue(is_fall_2026("2026 Autumn Co-op"))

    def test_not_fall_2026(self):
        self.assertFalse(is_fall_2026("Summer 2026 Internship"))
        self.assertFalse(is_fall_2026("Fall 2025 Internship"))
        self.assertFalse(is_fall_2026("2027 Fall Internship"))

    def test_tag_posting_fall_vs_generic_year(self):
        fall_posting = {"title": "Fall 2026 Accounting Intern", "description": ""}
        tags = tag_posting(fall_posting)
        self.assertIn("fall-2026", tags)
        self.assertIn("internship", tags)
        self.assertNotIn("2026", tags)

        year_posting = {"title": "2026 Summer Internship", "description": ""}
        tags = tag_posting(year_posting)
        self.assertIn("2026", tags)
        self.assertNotIn("fall-2026", tags)


class TestFilterModes(unittest.TestCase):
    def setUp(self):
        self.postings = [
            {
                "title": "Fall 2026 Finance Intern",
                "description": "",
                "location": "Salt Lake City, UT",
                "url": "https://a.example.com/1",
            },
            {
                "title": "Summer 2026 Accounting Intern",
                "description": "",
                "location": "Sandy, UT",
                "url": "https://a.example.com/2",
            },
            {
                "title": "Software Intern",
                "description": "",
                "location": "Draper, UT",
                "url": "https://a.example.com/3",
            },
            {
                "title": "Internal Audit Manager",
                "description": "",
                "location": "Salt Lake City, UT",
                "url": "https://a.example.com/4",
            },
            {
                "title": "Finance Intern",
                "description": "",
                "location": "New York, NY",
                "url": "https://a.example.com/5",
            },
        ]

    def tearDown(self):
        os.environ.pop("FILTER_MODE", None)
        os.environ.pop("LOCATION_KEYWORDS", None)

    def test_internship_mode_keeps_all_internships_default(self):
        os.environ["FILTER_MODE"] = "internship"
        result = filter_postings([dict(p) for p in self.postings])
        titles = {p["title"] for p in result}
        self.assertEqual(
            titles,
            {"Fall 2026 Finance Intern", "Summer 2026 Accounting Intern", "Software Intern"},
        )

    def test_fall2026_mode_only_explicit_fall(self):
        os.environ["FILTER_MODE"] = "fall2026"
        result = filter_postings([dict(p) for p in self.postings])
        titles = {p["title"] for p in result}
        self.assertEqual(titles, {"Fall 2026 Finance Intern"})

    def test_year2026_mode(self):
        os.environ["FILTER_MODE"] = "year2026"
        result = filter_postings([dict(p) for p in self.postings])
        titles = {p["title"] for p in result}
        self.assertEqual(titles, {"Fall 2026 Finance Intern", "Summer 2026 Accounting Intern"})

    def test_location_filter_drops_non_slc_non_remote(self):
        os.environ["FILTER_MODE"] = "internship"
        result = filter_postings([dict(p) for p in self.postings])
        urls = {p["url"] for p in result}
        self.assertNotIn("https://a.example.com/5", urls)


if __name__ == "__main__":
    unittest.main()
