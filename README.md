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

## Results: AQuA 8.2 (2026-10-29)

All 140 recordings. There are no listener MOS labels for this material, so
AQuA is compared with a reference MOS from an independent full-reference
objective metric, and with the nominal packet loss.

References: `hochdeutsch` uses `recordings/hochdeutsch/reference_audio.wav`
(the clean version). `female_voice` has none there, so
`reference_audio/female_voice_echo.wav` was used.

AQuA is AQuA 8.2.0 with `aqua_human.cfg` and `-normalize-mos on`: it reports the MOS
of the AQuA MOS Model `aqua-listener-2026.10b`, trained on listener MOS (NISQA,
TCD-VoIP) and Opus PLC. None of these recordings was used in training.

### Agreement with the reference MOS and with packet loss

r is Pearson correlation; ±0.5 is the share of files within 0.5 MOS of the
reference MOS; bias is the mean difference from it; drop is the mean MOS at 0%
loss minus the mean MOS at 30% loss.

| | r vs reference | ±0.5 | Bias | r vs loss | Drop |
|---|---|---|---|---|---|
| AQuA | 0.85 | 71% | −0.17 | −0.90 | 1.42 |
| Reference MOS | – | – | – | −0.88 | 2.02 |

### Mean MOS per packet-loss level (both talkers)

| | 0% | 5% | 10% | 15% | 20% | 25% | 30% |
|---|---|---|---|---|---|---|---|
| Reference MOS | 4.48 | 4.35 | 4.13 | 3.77 | 3.36 | 2.88 | 2.46 |
| AQuA | 4.13 | 4.03 | 3.87 | 3.41 | 3.22 | 2.91 | 2.70 |

### Monotonicity with packet loss

AQuA's mean MOS per talker.

| Talker | 0% | 5% | 10% | 15% | 20% | 25% | 30% |
|---|---|---|---|---|---|---|---|
| `female_voice` | 3.92 | 3.76 | 3.75 | 3.26 | 3.08 | 2.68 | 2.68 |
| `hochdeutsch` | 4.33 | 4.29 | 3.99 | 3.56 | 3.35 | 3.13 | 2.73 |
| Both talkers | 4.13 | 4.03 | 3.87 | 3.41 | 3.22 | 2.91 | 2.70 |

Per file: of all pairs of recordings of the same talker at different loss
levels, the share where the one with more loss scores lower; and the standard
deviation over the 10 runs of one condition, averaged over conditions.

| | Pairs ordered by loss | Run-to-run sd |
|---|---|---|
| AQuA | 94% | 0.16 |
| Reference MOS | 96% | 0.27 |

### Findings

- AQuA's mean MOS falls with every step of loss for both talkers, except that
  `female_voice` is flat over two steps: 5% to 10% (−0.01) and 25% to 30%
  (2.684 to 2.681). It orders 94% of file pairs by loss, close to the reference
  MOS (96%), and repeats better than it (run-to-run sd 0.16 against 0.27).
- Its correlation with loss (r −0.90) matches the reference MOS's (−0.88), but
  it covers only 1.42 of the reference's 2.02 MOS drop: it reads 0.35 below
  the reference at 0% loss and 0.25 above it at 30%.
- The conditions combine impairments: from 15% loss up, packet corruption and
  delay jitter rise with the loss rate, and Opus PLC conceals part of it, so
  monotonic here means monotonic with the whole condition.
- The AQuA model was partly trained on Opus PLC recordings of other talkers,
  labelled with the same reference metric, so its agreement with the reference
  MOS here is not fully independent.
