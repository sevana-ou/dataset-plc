#!/usr/bin/python3

import os
import sys
import sox
from pathlib import Path

def cut_audio(path_input: Path, path_output: Path, start_time: float, duration: float):
    # Create a SoX transformer
    transformer = sox.Transformer()

    # Trim the audio file starting from start_time and for the specified duration
    transformer.trim(start_time=start_time, end_time=start_time+duration)

    # Apply the transformation
    transformer.build(str(path_input), str(path_output))


def merge_audio(inputs: list[Path], path_output: Path):
    # Create a SoX combiner
    combiner = sox.Combiner()

    # Add input files to the combiner
    # for input_file in inputs:
    #    combiner.add_input_file(str(input_file))

    # Combine the input files into one output file
    input_list = [str(x) for x in inputs]
    combiner.build(input_list, str(path_output), 'concatenate')


def apply_echo(path_input, path_output: Path):
    if not path_input.exists():
        raise RuntimeError('Input file doesn\'t exist')

    in_gain = 0.6   # This is the echo volume. It determines how loud the echo will be compared to the original audio. You can adjust this value as needed.
    out_gain = 0.3  # This is the decay. It controls how much the echo fades over time. Lower values will make the echo fade out faster.
    delays = 200    # This is the delay in milliseconds. It determines how long it takes for the echo to be heard after the original sound.
    decays = 0.3    # This is the delay in seconds. It determines how long it takes for the effect to be applied. This can help you synchronize the echo effect with the original audio.
    
    # Permament echo (for all the file length)
    cmd = f'ffmpeg -i {path_input} -filter_complex "aecho={in_gain}:{out_gain}:{delays}:{decays}" {path_output}' 

    retcode = os.system(cmd)
    if retcode != 0:
        raise RuntimeError(f'ffmpeg non-zero exit code: {retcode}')
    

def get_audio_length(audio_file):
    # Use sox.file_info.info function to get information about the audio file
    info = sox.file_info.info(str(audio_file))

    # Extract duration from the audio file information
    duration = info['duration']

    return duration


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: apply_echo.py <input file> <output file>')
        exit(0)

    # Cut the source file into segments [0..5) and [5..end of file]
    path_input = Path(sys.argv[1])
    path_output = Path(sys.argv[2])

    cut_audio(path_input=path_input, path_output=Path('segment_1.wav'), start_time=0.0, duration=5.0)
    cut_audio(path_input=path_input, path_output=Path('segment_2.wav'), start_time=5.0, duration=get_audio_length(path_input) - 5.0)

    apply_echo(Path('segment_1.wav'), Path('segment_1_echo.wav'))
    merge_audio([Path('segment_1_echo.wav'), Path('segment_2.wav')], path_output)

