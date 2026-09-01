import unittest

from voice_cursor.screen_text import ScreenTextLocator


def tsv_with_words(words):
    header = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
        "left\ttop\twidth\theight\tconf\ttext\n"
    )
    rows = ["1\t1\t0\t0\t0\t0\t0\t0\t1000\t800\t-1\t"]
    for index, (text, left, top, width, height, confidence) in enumerate(
        words,
        start=1,
    ):
        rows.append(
            f"5\t1\t1\t1\t{index}\t1\t{left}\t{top}\t{width}\t"
            f"{height}\t{confidence}\t{text}"
        )
    return header + "\n".join(rows) + "\n"


def tsv_with_same_line_words(words):
    header = (
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
        "left\ttop\twidth\theight\tconf\ttext\n"
    )
    rows = ["1\t1\t0\t0\t0\t0\t0\t0\t1000\t800\t-1\t"]
    for index, (text, left, top, width, height, confidence) in enumerate(
        words,
        start=1,
    ):
        rows.append(
            f"5\t1\t1\t1\t1\t{index}\t{left}\t{top}\t{width}\t"
            f"{height}\t{confidence}\t{text}"
        )
    return header + "\n".join(rows) + "\n"


class ScreenTextTests(unittest.TestCase):
    def test_voice_cursor_rectangle_is_excluded_but_other_text_remains(self):
        matches = ScreenTextLocator.matches_from_tsv(
            tsv_with_words(
                [
                    ("hello", 90, 100, 80, 30, 95),
                    ("hello", 600, 500, 80, 30, 92),
                ]
            ),
            "hello",
            screen_width=1000,
            screen_height=800,
            excluded_rectangles=((50, 50, 250, 250),),
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual((matches[0].x, matches[0].y), (640, 515))

    def test_desktop_folder_name_can_be_located_as_ordinary_text(self):
        matches = ScreenTextLocator.matches_from_tsv(
            tsv_with_words([("Projects", 820, 120, 100, 28, 97)]),
            "projects",
            screen_width=1000,
            screen_height=800,
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].text, "Projects")

    def test_ocr_target_matching_is_word_sensitive(self):
        matches = ScreenTextLocator.matches_from_tsv(
            tsv_with_words([("Project", 820, 120, 100, 28, 97)]),
            "projects",
            screen_width=1000,
            screen_height=800,
        )
        self.assertEqual(matches, [])

    def test_ocr_combined_word_matches_spoken_separate_words(self):
        matches = ScreenTextLocator.matches_from_tsv(
            tsv_with_words([("BACKEND", 700, 120, 130, 28, 97)]),
            "back end",
            screen_width=1000,
            screen_height=800,
        )
        self.assertEqual([item.text for item in matches], ["BACKEND"])

    def test_ocr_separate_words_match_spoken_combined_word(self):
        matches = ScreenTextLocator.matches_from_tsv(
            tsv_with_same_line_words(
                [
                    ("Back", 700, 120, 60, 28, 97),
                    ("End", 768, 120, 55, 28, 96),
                ]
            ),
            "backend",
            screen_width=1000,
            screen_height=800,
        )
        self.assertEqual([item.text for item in matches], ["Back End"])


if __name__ == "__main__":
    unittest.main()
