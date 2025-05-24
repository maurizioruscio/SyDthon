import os
import struct
import numpy as np
from pydub import AudioSegment
import librosa

# -----------------------------------------------------------------------------
# Constants for SID timing
# -----------------------------------------------------------------------------
# Clock rates for audio chips
SID_CLOCKS = {
    '6581': 985248,   # PAL MOS6581
    '8580': 1022730,  # NTSC/MOS8580
}

# -----------------------------------------------------------------------------
# 1. Convert MP3 to WAV
# -----------------------------------------------------------------------------
def convert_mp3_to_wav(mp3_path, wav_path, target_sr=44100):
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_frame_rate(target_sr).set_channels(1)
    audio.export(wav_path, format="wav")
    print(f"Converted MP3 to WAV: {wav_path}")

# -----------------------------------------------------------------------------
# 2. Extract pitch track
# -----------------------------------------------------------------------------
def extract_pitch_track(wav_path, hop_length=512, fmin=50.0, fmax=2000.0):
    y, sr = librosa.load(wav_path, sr=None)
    pitches, magnitudes = librosa.piptrack(
        y=y, sr=sr, hop_length=hop_length,
        fmin=fmin, fmax=fmax
    )
    pitch_track = []
    for i in range(pitches.shape[1]):
        idx = magnitudes[:, i].argmax()
        pitch_track.append(pitches[idx, i])
    return np.array(pitch_track), librosa.frames_to_time(
        np.arange(len(pitch_track)), sr=sr, hop_length=hop_length
    )

# -----------------------------------------------------------------------------
# 3. Convert frequency to SID register value
# -----------------------------------------------------------------------------
def freq_to_sid_value(freq, chip='6581'):
    """
    Convert a frequency in Hz to a 16-bit SID frequency word.
    chip: '6581' for MOS6581 (PAL), '8580' for MOS8580 (NTSC).
    """
    if freq <= 0:
        return 0
    clock = SID_CLOCKS.get(chip, SID_CLOCKS['6581'])
    # 16-bit word: freq * 2^24 / clock
    value = int(np.round(freq * (1 << 24) / clock)) & 0xFFFF
    return value

# -----------------------------------------------------------------------------
# 4. Write PSID header for .sid v2
# -----------------------------------------------------------------------------
def write_sid_header(f, song_length=1, chip='6581'):
    # PSID magic
    f.write(b'PSID')
    # Version 2
    f.write(struct.pack('>H', 2))
    # Data offset (header size): 0x7C bytes
    f.write(struct.pack('>H', 0x007C))
    # Load address (0x1000)
    f.write(struct.pack('>H', 0x1000))
    # Init address
    f.write(struct.pack('>H', 0x1000))
    # Play address
    f.write(struct.pack('>H', 0x1003))
    # Songs count
    f.write(struct.pack('>H', song_length))
    # Start song
    f.write(struct.pack('>H', 1))
    # Flags: bit0 = PAL, bit1 = NTSC
    flags = 0
    if chip == '6581': flags |= 1
    if chip == '8580': flags |= 2
    f.write(struct.pack('>H', flags))
    # Reserved (2 bytes)
    f.write(b'\x00\x00')
    # Strings: Title, Author, Released (32 bytes each)
    for text in ("MP3->SID Converter", "Maurizio Ruscio", "2025"):  
        data = text.encode('ascii')[:32]
        f.write(data + b'\x00' * (32 - len(data)))

# -----------------------------------------------------------------------------
# Main conversion pipeline
# -----------------------------------------------------------------------------
def convert_mp3_to_sid(mp3_path, sid_path, chip='6581'):
    base, _ = os.path.splitext(mp3_path)
    wav_path = base + ".wav"
    convert_mp3_to_wav(mp3_path, wav_path)

    pitch_track, times = extract_pitch_track(wav_path)
    sid_values = [freq_to_sid_value(freq, chip) for freq in pitch_track]

    with open(sid_path, 'wb') as f:
        write_sid_header(f, song_length=1, chip=chip)
        # TODO: Append 6502 machine code player and SID data:
        # - Write initialization and main loop in 6510 assembly
        # - Embed sid_values as data to poke into SID voice registers
    print(f"SID file stub written: {sid_path}")

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Convert MP3 to C64 .SID (stub).'
    )
    parser.add_argument('input', help='Input MP3 file')
    parser.add_argument('output', nargs='?', help='Output SID file')
    parser.add_argument('--chip', choices=['6581','8580'], default='6581',
        help='Audio chip type: 6581 (PAL) or 8580 (NTSC)'
    )
    args = parser.parse_args()
    out_file = args.output or os.path.splitext(args.input)[0] + '.sid'
    convert_mp3_to_sid(args.input, out_file, chip=args.chip)
