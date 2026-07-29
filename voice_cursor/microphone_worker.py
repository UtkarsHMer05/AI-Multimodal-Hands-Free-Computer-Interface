"""Capture microphone PCM in a disposable process.

PortAudio/CoreAudio can abort the process on some macOS device failures. Keeping
the stream in this worker prevents that native crash from taking down the Tk
application and the already-loaded Parakeet recognizer.
"""

from __future__ import annotations

import argparse
import queue
import sys


def capture(*, device_index: int, sample_rate: int) -> int:
    import sounddevice as sd

    audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=120)

    def audio_callback(indata, _frames, _time, status) -> None:
        if status:
            print(f"Microphone status: {status}", file=sys.stderr, flush=True)
        try:
            audio_queue.put_nowait(bytes(indata))
        except queue.Full:
            pass

    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=0,
            device=device_index,
            dtype="int16",
            channels=1,
            latency="high",
            callback=audio_callback,
        ):
            output = sys.stdout.buffer
            while True:
                output.write(audio_queue.get())
                output.flush()
    except (BrokenPipeError, KeyboardInterrupt):
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-index", type=int, required=True)
    parser.add_argument("--sample-rate", type=int, required=True)
    arguments = parser.parse_args()
    return capture(
        device_index=arguments.device_index,
        sample_rate=arguments.sample_rate,
    )


if __name__ == "__main__":
    raise SystemExit(main())
