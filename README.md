# Opus packet-loss dataset

140 recordings of speech sent over Opus with network impairments: 2 talkers ×
7 packet-loss levels × 10 runs, 48 kHz mono, about 24 s each, with the
reference recordings they were made from. The repository shows how Sevana AQuA
scores them.

| Path | Contents |
|---|---|
| `reference_audio/` | Source recordings, clean and with echo (`*_echo.wav`) |
| `recordings/<talker>/` | Degraded recordings, plus `reference_audio.wav` for `hochdeutsch` |
| `generate/` | Echo and packet-loss generating scripts |
| `run_tests.py` | Scores the recordings with AQuA |
| `reference_mos.csv` | Per-file reference MOS and AQuA MOS behind the results below |

## Source audio and licences

The reference recordings come from freesound.org, via
[voxserv/audio_quality_testing_samples](https://github.com/voxserv/audio_quality_testing_samples).
Thanks to Stanislav for this collection! Each reference file, and every recording made from it,
keeps the licence of its source:

| Talker | Source | Licence |
|---|---|---|
| `female_voice` | [I am female](https://freesound.org/people/acclivity/sounds/34210/) by acclivity | [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), non-commercial use only |
| `hochdeutsch` | [Global Village Hochdeutsch](https://freesound.org/people/blaukreuz/sounds/165187/) by blaukreuz | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) |

## Running AQuA

AQuA is not included in the public repository; contact [Sevana](https://sevana.biz) for an
evaluation licence. `run_tests.py` expects it in `bin/`:

| File | Contents |
|---|---|
| `bin/aqua-wb` | AQuA 8.2 executable |
| `bin/aqua-wb.lic` | AQuA licence |
| `bin/aqua_human.cfg` | AQuA's default config |

```
./run_tests.py
```

It prints the mean MOS per talker and condition and writes every file's score to
`aqua_scores.csv`. Regenerating the recordings also needs Sevana's
`audio-channel` tool (`generate/tc/`), which is not included either.

## Generating

The scripts are in `generate/`; `ffmpeg` is needed.

1. Echoes are generated first (`apply_echo.py`, ffmpeg `aecho`). The result is
   used as the reference when generating the packet losses.
2. Packet losses (`tc/run_test.py`): `tc netem` on the loopback interface adds
   loss, corruption and delay jitter, and the `audio-channel` tool plays the
   reference over an Opus call (PLC on) and records the received audio.
   `make_gaps.py` is an alternative that cuts gaps into a file directly.

File names encode the conditions:

```
r_pl_<loss %>_nc_<corrupt %>_di_<delay ms>-<jitter ms>_plc_on_opus_<opus loss %>_iteration_<run>.wav
```

| Packet loss | Corruption | Delay ± jitter (ms) |
|---|---|---|
| 0% | 0% | 20 ± 5 |
| 5% | 0% | 20 ± 10 |
| 10% | 0% | 50 ± 20 |
| 15% | 1% | 100 ± 50 |
| 20% | 2% | 100 ± 50 |
| 25% | 3% | 100 ± 70 |
| 30% | 4% | 100 ± 70 |

The Opus encoder's expected loss is set to 5% in every condition.

## Results: AQuA 8.2, MOS model `aqua-listener-2026.11b` (2026-11-02)

All 140 recordings. There are no listener MOS labels for this material, so AQuA
is compared with a reference MOS estimated on the listener scale from an
independent full-reference objective metric, and with the nominal packet loss.

References: `hochdeutsch` uses `recordings/hochdeutsch/reference_audio.wav`
(the clean version). `female_voice` has none there, so
`reference_audio/female_voice_echo.wav` was used.

AQuA is AQuA 8.2.0 with `aqua_human.cfg` and `-normalize-mos on`: it reports the MOS
of the AQuA MOS Model `aqua-listener-2026.11b`, trained on listener MOS (NISQA,
TCD-VoIP) and Opus PLC. None of these recordings was used in training.

`reference_mos.csv` lists, per recording, the reference MOS (`reference_mos`) and
AQuA's MOS (`aqua_2026_11b`, as AQuA reports it, to two decimals).

### Agreement with the reference MOS and with packet loss

r is Pearson correlation; ±0.5 is the share of files within 0.5 MOS of the
reference MOS; bias is the mean difference from it; MAE the mean absolute
difference; drop is the mean MOS at 0% loss minus the mean MOS at 30% loss.

| | r vs reference | ±0.5 | Bias | MAE | r vs loss | Drop |
|---|---|---|---|---|---|---|
| AQuA | 0.90 | 65% | +0.28 | 0.47 | −0.92 | 2.49 |
| Reference MOS | – | – | – | – | −0.93 | 3.06 |

### Mean MOS per packet-loss level

| Talker | | 0% | 5% | 10% | 15% | 20% | 25% | 30% |
|---|---|---|---|---|---|---|---|---|
| Both talkers | Reference MOS | 4.26 | 4.02 | 3.61 | 2.95 | 2.24 | 1.54 | 1.19 |
| | AQuA | 4.21 | 4.10 | 3.73 | 3.12 | 2.77 | 2.14 | 1.72 |
| `female_voice` | Reference MOS | 4.22 | 3.96 | 3.75 | 3.18 | 2.56 | 1.55 | 1.30 |
| | AQuA | 3.88 | 3.72 | 3.73 | 3.04 | 2.74 | 1.72 | 1.68 |
| `hochdeutsch` | Reference MOS | 4.29 | 4.09 | 3.48 | 2.71 | 1.93 | 1.53 | 1.08 |
| | AQuA | 4.55 | 4.48 | 3.73 | 3.20 | 2.81 | 2.57 | 1.76 |

### Difference from the reference MOS

AQuA minus reference MOS, mean per condition, and in brackets the share of the
condition's 10 files within ±0.5 of it.

| Talker | 0% | 5% | 10% | 15% | 20% | 25% | 30% |
|---|---|---|---|---|---|---|---|
| Both talkers | −0.04 (95%) | +0.07 (80%) | +0.12 (95%) | +0.17 (75%) | +0.53 (45%) | +0.60 (25%) | +0.53 (40%) |
| `female_voice` | −0.34 (90%) | −0.24 (80%) | −0.02 (100%) | −0.13 (90%) | +0.18 (70%) | +0.17 (50%) | +0.38 (40%) |
| `hochdeutsch` | +0.26 (100%) | +0.39 (80%) | +0.25 (90%) | +0.48 (60%) | +0.88 (20%) | +1.04 (0%) | +0.68 (40%) |

### Monotonicity with packet loss

Per file: of all pairs of recordings of the same talker at different loss
levels, the share where the one with more loss scores lower; and the standard
deviation over the 10 runs of one condition, averaged over conditions.

| | Pairs ordered by loss | Run-to-run sd |
|---|---|---|
| AQuA | 93% | 0.25 |
| Reference MOS | 95% | 0.31 |

### Findings

- AQuA follows the reference MOS closely: r 0.90, bias +0.28, MAE 0.47, 65% of
  files within ±0.5, and a 2.49 MOS drop from 0% to 30% loss (reference: 3.06). Up
  to 15% loss it stays within 0.2 of the reference on average; the remaining error
  is at 20-30% loss, where it reads 0.5 to 0.6 too high.
- Ranking matches the reference: r −0.92 with loss (reference −0.93), and 93% of
  file pairs ordered by loss (reference 95%). Run-to-run spread is 0.25, below the
  reference MOS's 0.31.
- The remaining error depends on the talker. `hochdeutsch` reads too high at every
  level, most at 20-25% loss (+0.9 to +1.0); clean it reads 4.55 against 4.29.
  `female_voice`, whose reference carries echo, reads too low up to 15% loss (up to
  −0.34 at 0%) and within +0.4 above it from 20% up.
- AQuA's mean MOS falls with every step of loss for both talkers, except
  `female_voice` from 5% to 10% (3.717 to 3.730).
- The conditions combine impairments: from 15% loss up, packet corruption and
  delay jitter rise with the loss rate, and Opus PLC conceals part of it, so
  monotonic here means monotonic with the whole condition.
- The reference MOS is an estimate, not a listening test, and at 20-30% loss some
  files reach its 1.0 floor. Only a listening test on this material would settle
  the absolute level.
