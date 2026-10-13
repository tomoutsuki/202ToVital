# Validation

## Automated checks

The standard-library unittest suite checks P202 framing, duplicate/non-finite
parameters, exact single/bank correspondence for Pretty Pluck, all 47 source
presets, Vital scalar ranges, envelope and bipolar modulation units, routing,
FX bypass, deterministic assets, archive layout, name collisions, input/report
protection, selection, profiles, and strict-mode refusal.

Native validation uses optional Vita 0.1.0 with NumPy, installed into the project
virtual environment. It loads every generated bank member and renders a note,
checking finite samples and recording amplitude statistics. Results are saved to
`examples/native-validation.json`. This establishes load/render compatibility
with this Vita build, not with every Vital release or graphical bank importer.

Five controlled Poison recordings now permit a steady harmonic comparison of
single oscillator waveforms; see [the waveform review](controlled-waveform-review.md).
Broader sonic similarity, exact timing, filter response, FX sound and modulation
accuracy remain unverified.

## Recorded run

The 29 unittest cases pass. The installed `202tovital` entry point successfully
inspected the single export and converted the supplied bank. All 47 presets
loaded in Vita 0.1.0 and rendered finite, non-silent samples at 22,050 Hz,
MIDI note 60, velocity 0.7, a 0.35-second gate and a 0.75-second render.
With the final -18 dB output offset, the largest absolute sample was 0.928412;
no tested patch exceeded unity. This is one note/velocity, not a general peak bound.
A synthetic sine preset at MIDI 69 measured 440 Hz with an FFT.

`examples/PrettyPluck-preview.wav` is a three-second native preview of the
converted single preset. It is not a Poison reference or a similarity assessment.
