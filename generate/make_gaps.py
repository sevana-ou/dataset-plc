#!/usr/bin/python3

import sys
import wave
import random
import argparse
import os
from pathlib import Path

# How much length of audio file (in percents) will be filled with an audio impairments
GAP_PERCENTS = 40

# Single audio gap length limits in milliseconds
# To work properly the higher limit should be multiple of lower limit i.e. (100, 200) or (100, 400) etc.
GAP_INTERVAL = (100, 1000)

def process_file(input: Path, output: Path):
    # Open input file
    audio_input : wave.Wave_read = wave.open(open(input, 'rb'), 'rb')
    audio_input_params = audio_input.getparams()

    # Create output file
    audio_output : wave.Wave_write = wave.open(open(output, 'wb'), 'w')
    audio_output.setnchannels(audio_input.getnchannels())
    audio_output.setsampwidth(audio_input.getsampwidth())
    audio_output.setframerate(audio_input.getframerate())

    nr_of_frames = audio_input.getnframes()
    framerate = audio_input.getframerate()

    counter_of_total_gaps_frames = 0
    counter_of_current_gap_frames = 0

    # Length of minimal chunk in frames
    nr_of_chunk_frames = int((framerate / 1000) * GAP_INTERVAL[0])

    nr_of_chunks = int(nr_of_frames / nr_of_chunk_frames)
    for i in range(0, nr_of_chunks):
        d = audio_input.readframes(nr_of_chunk_frames)

        if i == 0 or counter_of_current_gap_frames >= nr_of_frames * GAP_PERCENTS / 100.0:
            # Keep the first chunk (and all chunks when generating done) without the problem
            pass
        else:
            # What is probability ?
            is_gap = random.randrange(0, 100) < GAP_PERCENTS

            # Ensure this gap is not bigger than specified
            if counter_of_current_gap_frames / (framerate / 1000) >= GAP_INTERVAL[1] and is_gap:
                is_gap = False

            if is_gap:
                # Here replace d with a silence
                d = bytes(len(d))

                # Increase the counters
                counter_of_current_gap_frames += nr_of_chunk_frames
                counter_of_total_gaps_frames += nr_of_chunk_frames
            else:
                counter_of_current_gap_frames = 0

        audio_output.writeframes(d)
    
    audio_input.close()
    audio_output.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inserts audio gaps to audio.')
    parser.add_argument('--input')
    parser.add_argument('--output')
    args = parser.parse_args()

    if args.input == args.output:
        print(f'Input and output files cannot be the same.')
        exit(os.EX_CONFIG)
    
    process_file(Path(args.input), Path(args.output))