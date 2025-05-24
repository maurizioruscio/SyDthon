# -----------------------------------------------------------------------------
# sid_player.py
# -----------------------------------------------------------------------------
import struct
from pysid.player import Player
from pysid import SIDFile
import sounddevice as sd


def play_sid_file(sid_path, duration=None, samplerate=44100):
    """
    Play a .sid file via pysid and sounddevice.
    sid_path: path to .sid file
    duration: seconds to play (None = full length)
    samplerate: audio output sample rate
    """
    sid = SIDFile(sid_path)
    player = Player(sid)
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    def callback(outdata, frames, time, status):
        samples = player.get_samples(frames)
        outdata[:] = samples.reshape(-1, 1)
    with sd.OutputStream(callback=callback):
        if duration:
            sd.sleep(int(duration * 1000))
        else:
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Play a C64 .SID file.'
    )
    parser.add_argument('sidfile', help='Path to .sid file')
    parser.add_argument('--duration', type=float,
        help='Seconds to play; full length if omitted')
    parser.add_argument('--samplerate', type=int, default=44100,
        help='Output sample rate')
    args = parser.parse_args()
    play_sid_file(args.sidfile, duration=args.duration, samplerate=args.samplerate)
