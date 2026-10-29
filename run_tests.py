#!/usr/bin/python3
# Scores every recording with AQuA and prints the mean MOS per talker and test condition.
import csv
import multiprocessing
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

import utils_sevana

DIR_THIS = Path(__file__).parent.resolve()

# hochdeutsch carries its reference next to the recordings;
# female_voice was recorded from the echo version in reference_audio/
REFERENCES = {
    'female_voice': DIR_THIS / 'reference_audio/female_voice_echo.wav',
    'hochdeutsch': DIR_THIS / 'recordings/hochdeutsch/reference_audio.wav',
}

PATTERN = re.compile(r'r_pl_(?P<ploss>\d+)_nc_(?P<nc>\d+)_di_(?P<delay>\d+)-(?P<delay_radius>\d+)'
                     r'_plc_on_opus_(?P<reserved>\d+)_iteration_(?P<iteration>\d+)\.wav')


@dataclass
class Test:
    talker: str
    path: Path
    packet_loss: int
    network_corrupt: int
    delay: int
    delay_radius: int
    iteration: int
    mos: float = None


def collect() -> list[Test]:
    tests = []
    for talker in REFERENCES:
        for p in sorted((DIR_THIS / 'recordings' / talker).glob('r_pl_*.wav')):
            m = PATTERN.match(p.name)
            tests.append(Test(talker, p, int(m['ploss']), int(m['nc']), int(m['delay']), int(m['delay_radius']),
                              int(m['iteration'])))
    return tests


def score(test: Test) -> Test:
    test.mos, _ = utils_sevana.find_aqua_mos(REFERENCES[test.talker], test.path)
    return test


if __name__ == '__main__':
    tests = collect()
    with multiprocessing.Pool() as pool:
        tests = pool.map(score, tests)

    with open(DIR_THIS / 'aqua_scores.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['talker', 'file', 'packet_loss', 'iteration', 'mos'])
        for t in tests:
            w.writerow([t.talker, t.path.name, t.packet_loss, t.iteration, t.mos])

    for talker in REFERENCES:
        print(talker)
        for loss in sorted({t.packet_loss for t in tests}):
            cell = [t for t in tests if t.talker == talker and t.packet_loss == loss and t.mos is not None]
            if cell:
                c = cell[0]
                print(f'    loss {loss:02d}%, corrupt {c.network_corrupt}%, delay {c.delay}+-{c.delay_radius} ms: '
                      f'MOS {statistics.mean(t.mos for t in cell):.2f} ({len(cell)} runs)')
