import unittest

from voice_cursor.commands import (
    CommandName,
    ScreenActionKind,
    evaluation_commands,
    interpret_command,
    interpret_screen_text_action,
    normalize_phrase,
    recognition_phrases,
)


class CommandTests(unittest.TestCase):
    def test_normalizes_punctuation_and_spacing(self):
        self.assertEqual(normalize_phrase("  Move,   LEFT! "), "move left")

    def test_accepts_polite_prefix(self):
        command = interpret_command("Please move right")
        self.assertIsNotNone(command)
        self.assertEqual(command.name, CommandName.MOVE_RIGHT)

    def test_matches_alias(self):
        command = interpret_command("enable control")
        self.assertIsNotNone(command)
        self.assertEqual(command.name, CommandName.RESUME_CONTROL)

    def test_matches_screen_aware_click_enable(self):
        action = interpret_screen_text_action("click enable")
        self.assertIsNotNone(action)
        self.assertEqual(action.kind, ScreenActionKind.CLICK)
        self.assertEqual(action.label, "enable")

    def test_matches_multiword_double_click(self):
        action = interpret_screen_text_action("double click on the sign in")
        self.assertIsNotNone(action)
        self.assertEqual(action.kind, ScreenActionKind.DOUBLE_CLICK)
        self.assertEqual(action.label, "sign in")

    def test_dynamic_label_preserves_digits(self):
        action = interpret_screen_text_action("click Page 2")
        self.assertIsNotNone(action)
        self.assertEqual(action.label, "page 2")

    def test_plain_click_remains_a_cursor_command(self):
        self.assertIsNone(interpret_screen_text_action("click"))
        command = interpret_command("click")
        self.assertIsNotNone(command)
        self.assertEqual(command.name, CommandName.LEFT_CLICK)

    def test_rejects_unlisted_phrase(self):
        self.assertIsNone(interpret_command("delete all files"))

    def test_recovers_clear_asr_error_for_close_tab(self):
        command = interpret_command("close sab")
        self.assertIsNotNone(command)
        self.assertEqual(command.name, CommandName.CLOSE_TAB)

    def test_recovers_clear_asr_error_for_pause_control(self):
        command = interpret_command("pass control")
        self.assertIsNotNone(command)
        self.assertEqual(command.name, CommandName.PAUSE_CONTROL)

    def test_grammar_contains_unknown_token(self):
        self.assertIn("[unk]", recognition_phrases())

    def test_evaluation_excludes_control_toggles(self):
        names = {command.name for command in evaluation_commands()}
        self.assertNotIn(CommandName.PAUSE_CONTROL, names)
        self.assertNotIn(CommandName.RESUME_CONTROL, names)
        self.assertEqual(len(names), 12)


if __name__ == "__main__":
    unittest.main()
