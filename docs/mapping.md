# Mapping decisions and known fidelity limits

The primary Poison reference is the user-authored
`../.materials/Poison202Features.md` (2026-10-09 research draft). Its evidence
legend explicitly distinguishes observed UI from hypotheses. There are no
Poison reference renders or controlled one-parameter exports in this corpus.
Do not label these mappings acoustically verified.

## Oscillators, envelopes and routing

`O1TY`/`O2TY` are provisionally ordered saw, pulse, sine, triangle, supersaw.
Wave Source assets are generated from analytic waveforms except for Super Saw,
which loads the packaged `data/JP_inspired_HP2_fc_1p5xF0_2048.wav` float32 table
verbatim. Pulse width assumes normalized PW maps 50%..99% duty. A controlled
Super Saw MIX/DETUNE sweep supports a JP-8000/Szabo-style model. The converter
preserves a strict one-to-one oscillator mapping: Poison OSC1 maps only to Vital
OSC1 and Poison OSC2 maps only to Vital OSC2. Each Super Saw uses seven voices in
that oscillator slot, normal unison stack, zero stereo spread, 180-degree phase,
full random phase, and the embedded 2048-sample `JP_inspired_HP2_fc_1p5xF0`
single-cycle wavetable supplied for this conversion. No auxiliary Vital oscillator
or harmonic layer is allocated to reproduce one Poison oscillator.

MIX maps through the fitted JP center/per-side gain ratio into Vital Blend.
DETUNE maps through the fitted nonlinear Poison curve. Because Vital's voice
positions are symmetric, the target outer spread is the mean absolute distance
of Szabo's measured -201.79/+176.69-cent pair rather than either side alone.
Detune Power 1.09 is a one-parameter fit to the averaged inner, middle and outer
JP pairs using Vital's exponential `powerScale()` law. The fit is intentionally
approximate: at full DETUNE Vital produces symmetric pairs near +/-42.0,
+/-102.4 and +/-189.2 cents, versus averaged JP targets of +/-34.1, +/-108.4 and
+/-189.2 cents. It cannot preserve the individual asymmetric signs.

Vital's serialized `unison_detune` uses quadratic scaling: physical outer spread
is `detune_range * unison_detune**2`. The converter therefore writes
`sqrt(outer_cents / detune_range)` rather than copying a displayed knob value.
The controlled recordings still show unresolved waveform coloration,
MIX-dependent harmonic balance, phase behavior and absolute-level differences.
The current JP-inspired HP2 asset improves the waveform baseline but does not
establish an exact reconstruction of Roland's pitch-dependent filtering or
aliasing. Fine tuning assumes +/-100 cents; tune range is configurable.

The IPA's `jimsawopen64x1024.data` contains 64 pitch-indexed, band-limited
1,024-sample saw tables. It is not a morph wavetable or a complete Super Saw
render. A separate `computeSuperSawDetuneForOsc(int)` symbol corroborates runtime
detune processing. The converter therefore does not embed `jimsawopen64x1024`
as a Vital wavetable, and this discovery does not turn the current Super Saw
MIX/DETUNE fits into exact reverse-engineered laws.

Balance is provisionally a linear crossfade in acoustic amplitude, converted
through Vital's square-root level encoding. Amp ADSRs use ENV2/ENV3, filter ADSRs
ENV4/ENV5, and pitch ADs use one-shot LFO3/LFO4. This leaves ENV1 available for
Vital's mandatory voice amplitude envelope. Pitch AD start/contour is inferred.

Parallel routing approximates each Poison TVA using its oscillator level before
the branch filter. Poison's documented order is oscillator -> TVF -> TVA; thus
filter tails and resonant behavior differ. ENV1 holds sustain 1 and releases at
the longest branch release, multiplying the branch releases again. Oscillator
level and ENV1 are squared in Vital: envelope contour is not preserved exactly.
The converter reports this rather than claiming two exact independent TVAs.

Series routing uses OSC1 + (OSC2 * TVA2) -> filter1 -> filter2 -> ENV1(TVA1).
This follows the user's described diagram more closely. `STRU=1` is assumed to
select series. Sub/noise are injected into filter1 and follow TVA1; their original
insertion point and sub waveform are unknown. Sub uses a sine at -12/-24 semitones
based on STYP; noise is a seeded one-second looping PCM sample, not a stochastic
unbounded generator. Vital's oscillator 3 supplies the sub.

Relevant Vital sources: `src/synthesis/modules/filters_module.cpp:100`,
`src/synthesis/modules/synth_voice_handler.cpp:278`,
`src/synthesis/modules/producers_module.cpp:43`, and
`src/common/synth_parameters.cpp:353` in the local Vital reference.

## Filters and timing

Filter selector 0 is assumed bypass, then LP/BP/HP/Peak/Notch. Analog 12dB filters
use blend/style settings; Peak/Notch responses approximate Poison. TVF PAIRED
is reported unsupported, since copying filter settings or adding poles would
invent behavior. SOFT RESO is reported unsupported for the same reason.

The default calibration profile proposes envelope seconds = 10*x**3 and cutoff
20*1000**x Hz. Free-running LFO RATE uses the temporary measured approximation
`max(lfo_min_hz, 40*x**2)`: the Poison experiment measured about 2.6, 10.3,
22.6 and 40 Hz at RATE 25, 50, 75 and 100. `lfo_min_hz` is a Vital-safe floor
at unmeasured RATE zero; `lfo_max_hz` and `lfo_rate_exponent` retain the curve
as profile settings rather than asserting it as identified Poison DSP. Fine
tuning, filter/pitch modulation limits and EQ range are similarly configurable.
LFO pitch uses the provisional signed curve
`lfo_pitch_semitones * sign(x) * abs(x)**lfo_pitch_exponent`, with defaults of
24 semitones and exponent 3.3. That curve fits the reported control geometry
(roughly MIDI 114--117 for about +11.8 semitones), but has not been verified by
audio measurement. P202 stores the signed normalized float `x`; the inspect
command displays that raw value and only labels the corresponding MIDI number as
an estimate.
Vital modulation amount is divided by the destination's parameter span; bipolar
amounts are doubled because Vital shifts the source by -0.5. See
`modulation_connection_processor.cpp:94`.

Tempo uses the draft's uncertain 22-entry division list and assumes a normalized
selector index. It chooses the nearest Vital straight/dotted/triplet division,
reporting approximations. Each Poison LFO pitch, filter and amplitude depth is
routed to both oscillator/filter branches. Positive and negative source depth
stays signed in a bipolar Vital connection. Poison's sine selector uses Vital's
built-in three-point smooth `Sin` shape; it is not sampled into a custom point
list. Normal LFOs reset at phase zero and random LFOs reset per note as a
deliberate export policy, independent of Poison RETRIG; the matching Poison
reset-phase offset remains unmeasured. Random uses Vital's sample-and-hold
generator. Random fade and LFO XFM are not implemented.

## Modulation and effects

XMOD is a dedicated conversion stage that assumes OSC1 carrier and OSC2
modulator and maps to Vital `FM <- OSC2` (phase mode 7). The profile maps the
normalized Poison control to effective FM depth as
`xmod_depth_max * XMOD ** xmod_depth_power`; the serialized Vital knob is the
square root of that result because Vital squares FM controls internally. The
default maximum/power of 1/1 preserve a linear effective-depth hypothesis, not
a measured calibration. The conversion report records the source depth,
effective depth, serialized amount, topology and confidence separately.

Velocity and wheel modulation use the same curve to match the full-source
endpoint: each Vital modulation amount is the difference between the base knob
and the knob at `min(1, XMOD + source_depth)`. Intermediate response and combined
velocity+wheel behavior remain approximate because Vital adds modulation after
the nonlinear Poison curve hypothesized here. Super Saw XMOD is explicitly
reported as experimental because Poison's internal per-voice routing is unknown.
This is not proof of Poison's cross-modulation algorithm or even its direction.
Ring uses RM from OSC2 (mode 10), taking priority if both are active; all static
and dynamic XMOD routes are then omitted and reported. Poison
oscillator-to-oscillator hard sync is omitted: Vital self-sync does not implement
the same dependency. Dynamic PWM is omitted because its routing is unverified.
See `synth_oscillator.h:116` and `producers_module.h:43` for Vital mode and source
selection; Poison202Features sections 4.1/4.4/8 explicitly flag the unknowns.

Velocity controls amp/filter/XMOD, wheel controls selected filter/pitch/XMOD and
adds to existing LFO depths. Exact response curves and wheel semantics remain
estimated. Portamento time, slide and patch gain use plausible inferred mappings.
The profile defaults to a -18 dB output offset after patch gain because native
rendering at 0 dB clipped even the synthetic sine case. This provides headroom,
not matched Poison loudness or a guarantee against clipping on every note/chord.
KPOS is classified as a non-sonic keyboard position. Unrecognized tags are never
discarded silently: inspection/report preserves their values with unmapped status.

FX selector 0 is assumed off, 1/2 correspond to the named alternatives. Global
FXON bypass is honored; EQ is separate. Distortion, bit-crush, chorus, flanger,
delay, ping-pong delay and reverb use corresponding Vital effects with approximate
parameter assignments. Crusher's second control, exact effect order and master
limiter cannot be reconstructed. Vital's default effect order is used. EQ assumes
+/-12 dB at Vital default frequencies. No master limiter tag has been identified.

## Next calibration experiments

1. Export an initialized preset, then change exactly one control per export.
   Confirm selector orders (especially filter bypass), tag meanings and ranges.
2. Render sine notes with FINE at minimum/zero/maximum to fit cents scaling.
3. Capture isolated amp/filter/pitch envelopes at several control values, fit
   timing and curvature, then update the calibration profile.
4. Measure filter response and resonance; characterize PAIRED and SOFT RESO.
5. Measure sync, PWM, XFM and FX behavior with isolated oscillator/effect sweeps.
6. Compare normalized loudness, spectra, transient timing and listening results
   at several MIDI notes/velocities. Vita can render converted patches, but it
   cannot render Poison without recordings supplied from the original synth.
