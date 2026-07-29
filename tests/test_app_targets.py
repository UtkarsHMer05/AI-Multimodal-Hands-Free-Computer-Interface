import unittest

from voice_cursor.app import VoiceCursorApp


class ProjectButtonTargetTests(unittest.TestCase):
    def app_with_targets(self):
        app = VoiceCursorApp.__new__(VoiceCursorApp)
        app.local_button_targets = [
            (object(), "Enable", ()),
            (object(), "Pause", ()),
            (object(), "Test Cursor", ("cursor test",)),
            (
                object(),
                "Start Guided Evaluation",
                ("start evaluation", "test evaluation", "test evaluations"),
            ),
        ]
        return app

    def test_enable_matches_real_button_registry(self):
        matches = self.app_with_targets()._matching_project_buttons("enable")
        self.assertEqual([item[1] for item in matches], ["Enable"])

    def test_transcript_sentence_is_not_a_button(self):
        matches = self.app_with_targets()._matching_project_buttons("click enable")
        self.assertEqual(matches, [])

    def test_test_evaluations_alias_matches_guided_evaluation_button(self):
        matches = self.app_with_targets()._matching_project_buttons(
            "test evaluations"
        )
        self.assertEqual(
            [item[1] for item in matches],
            ["Start Guided Evaluation"],
        )


if __name__ == "__main__":
    unittest.main()
