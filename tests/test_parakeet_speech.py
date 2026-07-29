import unittest
from array import array

from voice_cursor.parakeet_speech import UtteranceSegmenter, pcm16_rms


def pcm(value: int, frames: int) -> bytes:
    return array("h", [value] * frames).tobytes()


class ParakeetSpeechTests(unittest.TestCase):
    def test_pcm16_rms(self):
        self.assertEqual(pcm16_rms(pcm(1000, 100)), 1000)
        self.assertEqual(pcm16_rms(b""), 0)

    def test_segmenter_emits_one_phrase_after_trailing_silence(self):
        sample_rate = 1000
        segmenter = UtteranceSegmenter(
            sample_rate,
            calibration_seconds=0.2,
            silence_seconds=0.3,
            minimum_seconds=0.2,
        )
        blocks = [
            pcm(0, 100),
            pcm(0, 100),
            pcm(2000, 100),
            pcm(2000, 100),
            pcm(2000, 100),
            pcm(0, 100),
            pcm(0, 100),
            pcm(0, 100),
        ]
        results = [segmenter.feed(block) for block in blocks]
        utterances = [result for result in results if result is not None]
        self.assertEqual(len(utterances), 1)
        self.assertGreaterEqual(len(utterances[0]), 1_200)

    def test_quiet_audio_never_becomes_an_utterance(self):
        segmenter = UtteranceSegmenter(1000, calibration_seconds=0.2)
        results = [segmenter.feed(pcm(30, 100)) for _ in range(20)]
        self.assertTrue(all(result is None for result in results))


if __name__ == "__main__":
    unittest.main()
