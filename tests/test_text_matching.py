import unittest

from voice_cursor.text_matching import (
    normalize_target_text,
    target_comparison_key,
    target_texts_match,
)


class TargetTextMatchingTests(unittest.TestCase):
    def test_normalization_keeps_readable_words(self):
        self.assertEqual(normalize_target_text("  BACK-End! "), "back end")

    def test_key_ignores_case_spaces_and_separators(self):
        keys = {
            target_comparison_key(value)
            for value in ("backend", "back end", "BACKEND", "BACK-END")
        }
        self.assertEqual(keys, {"backend"})

    def test_different_spellings_remain_different(self):
        self.assertFalse(target_texts_match("project", "projects"))
        self.assertFalse(target_texts_match("backend", "backends"))

    def test_empty_labels_do_not_match(self):
        self.assertFalse(target_texts_match("", ""))


if __name__ == "__main__":
    unittest.main()
