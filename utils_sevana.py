#!/usr/bin/python3
import re
import subprocess
import tempfile

from pathlib import Path

DIR_THIS = Path(__file__).resolve().parent

AQUA_PATH = DIR_THIS / 'bin/aqua-wb'
AQUA_LIC_PATH = DIR_THIS / 'bin/aqua-wb.lic'
AQUA_CFG = DIR_THIS / 'bin/aqua_human.cfg'


# Runs AQuA on reference and test files; returns (MOS, percent) or (None, None) on failure.
# The MOS is that of the config's AQuA MOS Model (-normalize-mos on).
def find_aqua_mos(reference: Path, test_path: Path):
    cmd = [str(AQUA_PATH), str(AQUA_LIC_PATH), '-config', str(AQUA_CFG), '-src', 'file', str(reference),
           '-tstf', str(test_path), '-normalize-mos', 'on']
    # AQuA writes its fault and spectrum reports into the working directory
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if p.returncode != 0:
        print(f'AQuA returned error code {p.returncode}: {p.stdout}{p.stderr}')
        return None, None

    mos = re.search(r'MOS value\s+([\d.]+)', p.stdout)
    percent = re.search(r'Percent value\s+([\d.]+)', p.stdout)
    if not mos:
        print(f'No MOS in AQuA output: {p.stdout}')
        return None, None
    return float(mos.group(1)), float(percent.group(1)) if percent else None
