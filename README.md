# 202ToVital

Python CLI for converting Poison-202 `.p202` exports into self-contained Vital
`.vital` presets, `.vitalbank` bundles, or a directory of individual presets.
Requires Python 3.10+; conversion uses the standard library only.

**This is an experimental, uncalibrated converter.** Binary decoding is verified
against the supplied single preset and 47-preset bank. Vital output is checked
against its source and exercised with Vita. Five controlled Poison recordings
support a close steady harmonic match for the basic waveforms at matched pitch,
but Super Saw differs and broader perceptual fidelity remains unverified.
Each conversion writes a report explaining assumptions, unsupported features,
raw parameters, and any clipping. Read it before evaluating the result.

## Run

From this directory (`202ToVital/202ToVital`, the inner project):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/202tovital inspect ../.materials/SynthUserBank.p202
.venv/bin/202tovital convert ../.materials/SinglePreset.p202 -o PrettyPluck.vital
.venv/bin/202tovital convert ../.materials/SynthUserBank.p202 -o UserBank.vitalbank
.venv/bin/202tovital convert ../.materials/SynthUserBank.p202 --preset 39 -o Selected.vital
.venv/bin/202tovital convert ../.materials/SynthUserBank.p202 --format directory -o converted/
```

No-install alternative: prefix `python3 -m poison202_to_vital` with `PYTHONPATH=src`.
Example: `PYTHONPATH=src python3 -m poison202_to_vital inspect input.p202`.

Use `--preset "Pretty Pluck"` for an exact name (duplicate names require an index).
Use `--bpm 128` to set tempo, `--bank-name "My Bank"` to name the bank folder,
and `--report details.json` to choose the report path. Reports default to
`OUTPUT.report.json`, or `conversion-report.json` in directory mode.
Existing files are protected; `--force` explicitly permits replacement.
A multi-preset input needs `--preset` when producing one `.vital`.

`--strict` refuses unsupported/unknown/missing parameters and clipped values.
It does **not** certify acoustic fidelity. Most complex Poison patches require
best-effort conversion without this flag. All approximations remain in reports
and the Vital preset comments.

## Calibration

```sh
202tovital profile -o calibration.json
# Edit measured values or enum orders in calibration.json.
202tovital convert patch.p202 -o patch.vital --profile calibration.json
```

The profile exposes envelope timing/exponent, cutoff bounds, fine tuning,
pitch/filter modulation depths, LFO rate bounds, portamento, EQ gain, output
headroom (`output_gain_db`, default -18 dB), and
waveform/filter/LFO enum order. Defaults are explicit hypotheses. Numeric mapping
curves do not become measurements merely because they are configurable.
See [mapping notes](docs/mapping.md) and [format evidence](docs/format.md).

## Validation

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
# Optional native load/render tests; not required for conversion:
.venv/bin/python -m pip install vita numpy
PYTHONPATH=src .venv/bin/python tools/validate_native.py examples/SynthUserBank.vitalbank
```

The native validator checks loading, finite samples, reports peaks/RMS, and writes
JSON results. It does not compare against Poison audio. See
[validation results](docs/validation.md) for the actual checks performed.
The [controlled waveform review](docs/controlled-waveform-review.md) compares
five user-supplied Poison recordings with converted Vital presets at matched
MIDI pitch and records the remaining Super Saw mapping gap.

## Knowledge graph

The project graph indexes the Python implementation and these research notes.
It deliberately excludes vendor repositories, binary presets, generated reports,
and virtual environments. Source references in the notes identify the relevant
Vital implementation and original Poison observations.

```sh
graphify query "How do Poison amp envelopes map to Vital?" --budget 1500
graphify query "P202 record offsets float parameters" --budget 1500
graphify path "convert" "serialize"
```

Open `graphify-out/graph.html` for the interactive graph, or
`graphify-out/GRAPH_REPORT.md` for the audit. Structural updates can use
`graphify update .`; changed documentation needs semantic extraction via the
`graphify` skill. No provider key is required for the host-agent workflow.

## Project layout

- `src/poison202_to_vital/`: parser, calibration, mapping, Vital assets and CLI.
- `tests/`: malformed input, mapping units, real source fixtures and file safety.
- `tools/`: source-derived schema generator, native validation, graph build helper.
- `docs/`: evidence, assumptions and validation results.
- `examples/`: converted supplied presets and reports (generated, not tracked).

The original materials and Vita clone are read-only references outside this Git
repository. Generated periodic waveforms and white-noise samples are synthesized
by this project; no third-party preset/wavetable content is redistributed.
