import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.filters import filter_postings, is_fall_2026, is_internship, tag_posting


def posting(title="", description="", **kwargs):
    return {"title": title, "description": description, **kwargs}


class TestInternshipTitleMatching(unittest.TestCase):
    def test_matches_internship_variants(self):
        positives = [
            "Summer Internship",
            "Software Intern",
            "Interns wanted",
            "Co-op Program",
            "Coop position",
            "Co-Ops available",
        ]
        for title in positives:
            with self.subTest(title=title):
                self.assertTrue(is_internship(posting(title=title)))

    def test_matches_finance_internship_title_conventions(self):
        positives = [
            "Summer Analyst - Investment Banking",
            "Summer Associate, Corporate Finance",
            "Rotational Program - Finance",
            "2026 Finance Rotational Program",
        ]
        for title in positives:
            with self.subTest(title=title):
                self.assertTrue(is_internship(posting(title=title)))

    def test_does_not_match_internal_or_international(self):
        negatives = [
            "Internal Audit Analyst",
            "International Tax Associate",
            "Head of Internal Communications",
            "International Business Manager",
        ]
        for title in negatives:
            with self.subTest(title=title):
                self.assertFalse(is_internship(posting(title=title)))


class TestDescriptionFallback(unittest.TestCase):
    def test_title_match_wins_even_with_clean_description(self):
        p = posting(title="Finance Intern", description="Join our team for the summer.")
        self.assertTrue(is_internship(p))

    def test_description_fallback_catches_generic_title(self):
        p = posting(
            title="Early Career Program - Summer",
            description="This paid internship runs June through August.",
        )
        self.assertTrue(is_internship(p))

    def test_description_mention_near_qualification_words_is_ignored(self):
        # Real-world case: a full-time Paralegal posting whose description
        # merely *prefers* candidates with past internship experience.
        p = posting(
            title="Paralegal",
            description="Bachelor's degree in the law preferred (paralegal or "
            "legal internship experience, or even a general interest).",
        )
        self.assertFalse(is_internship(p))

    def test_description_mention_far_from_qualification_words_still_matches(self):
        p = posting(
            title="Student Program Associate",
            description="This role is a 12-week internship based in Salt Lake City. "
            "Housing assistance is provided for the summer.",
        )
        self.assertTrue(is_internship(p))


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
        tags = tag_posting(posting(title="Fall 2026 Accounting Intern"))
        self.assertIn("fall-2026", tags)
        self.assertIn("internship", tags)
        self.assertNotIn("2026", tags)

        tags = tag_posting(posting(title="2026 Summer Internship"))
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
