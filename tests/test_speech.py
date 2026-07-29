import unittest

from voice_cursor.speech import choose_recognition_text, input_device_candidates


class FakeSoundDevice:
    class Default:
        device = [0, 1]

    default = Default()

    @staticmethod
    def query_devices():
        return [
            {
                "name": "Bluetooth Headset",
                "max_input_channels": 1,
                "default_samplerate": 16000,
            },
            {
                "name": "MacBook Air Speakers",
                "max_input_channels": 0,
                "default_samplerate": 48000,
            },
            {
                "name": "MacBook Air Microphone",
                "max_input_channels": 1,
                "default_samplerate": 48000,
            },
            {
                "name": "Steam Streaming Microphone",
                "max_input_channels": 2,
                "default_samplerate": 44100,
            },
        ]


class InputDeviceTests(unittest.TestCase):
    def test_built_in_microphone_is_preferred(self):
        candidates = input_device_candidates(FakeSoundDevice(), None)
        self.assertEqual(candidates[0].name, "MacBook Air Microphone")
        self.assertEqual(candidates[0].sample_rate, 48000)
        self.assertEqual(candidates[-1].name, "Steam Streaming Microphone")

    def test_dynamic_free_speech_wins_for_screen_action(self):
        selected = choose_recognition_text("click", "click account settings")
        self.assertEqual(selected, "click account settings")

    def test_valid_fixed_command_wins_over_non_action_free_text(self):
        selected = choose_recognition_text("move left", "the left")
        self.assertEqual(selected, "move left")

    def test_requested_name_selects_one_device(self):
        candidates = input_device_candidates(FakeSoundDevice(), "Bluetooth")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].index, 0)

    def test_requested_index_selects_one_device(self):
        candidates = input_device_candidates(FakeSoundDevice(), "2")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].name, "MacBook Air Microphone")


if __name__ == "__main__":
    unittest.main()
