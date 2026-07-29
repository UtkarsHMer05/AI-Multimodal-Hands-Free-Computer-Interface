import csv
import tempfile
import unittest
from pathlib import Path

from voice_cursor.commands import interpret_command
from voice_cursor.evaluation import EvaluationSession


def commands(*phrases):
    matches = tuple(interpret_command(phrase) for phrase in phrases)
    assert all(matches)
    return matches


class EvaluationTests(unittest.TestCase):
    def test_records_accuracy_and_average_time(self):
        session = EvaluationSession(commands("move left", "click"))
        session.record("move left", elapsed=1.0)
        session.record("right click", elapsed=3.0)

        summary = session.summary()
        self.assertEqual(summary["total_trials"], 2)
        self.assertEqual(summary["correct_trials"], 1)
        self.assertEqual(summary["accuracy_percent"], 50.0)
        self.assertEqual(summary["average_response_seconds"], 2.0)

    def test_timeout_counts_as_incorrect(self):
        session = EvaluationSession(commands("scroll up"))
        session.record_timeout(elapsed=8.0)
        self.assertTrue(session.complete)
        self.assertFalse(session.trials[0].correct)
        self.assertEqual(session.trials[0].recognized_text, "")

    def test_exports_csv(self):
        session = EvaluationSession(commands("new tab"))
        session.record("new tab", elapsed=0.75)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = session.export_csv(Path(temp_dir))
            self.assertTrue(output.exists())
            with output.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.reader(csv_file))
            self.assertEqual(rows[0][0], "target_command")
            self.assertEqual(rows[1][3], "True")


if __name__ == "__main__":
    unittest.main()
