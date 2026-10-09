# Mapping decisions and known fidelity limits

The primary Poison reference is the user-authored
`../.materials/Poison202Features.md` (2026-10-09 research draft). Its evidence
legend explicitly distinguishes observed UI from hypotheses. There are no
Poison reference renders or controlled one-parameter exports in this corpus.
Do not label these mappings acoustically verified.

## Oscillators, envelopes and routing

`O1TY`/`O2TY` are provisionally ordered saw, pulse, sine, triangle, supersaw.
Wave Source assets are generated from analytic waveforms, with no external table
files. Pulse width assumes normalized PW maps 50%..99% duty. Super Saw uses seven
Vital unison voices, PW as unison blend and PM as detune. Poison mix/detune laws
are not known. Fine tuning assumes +/-100 cents; tune range is configurable.

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

The default calibration profile proposes envelope seconds = 10*x**3; cutoff
20*1000**x Hz; LFO 0.05*500**x Hz. These are chosen practical starting curves,
**not fitted measurements**. Fine tuning, filter/pitch modulation limits and EQ
range are similarly configurable. Vital modulation amount is divided by the
destination's parameter span; bipolar amounts are doubled because Vital shifts
the source by -0.5. See `modulation_connection_processor.cpp:94`.

Tempo uses the draft's uncertain 22-entry division list and assumes a normalized
selector index. It chooses the nearest Vital straight/dotted/triplet division,
reporting approximations. LFO1 is provisionally routed to branch1 and LFO2 to
branch2. Random uses Vital's sample-and-hold generator. Random fade and LFO XFM
are not implemented. Wave phase, routing and retrigger semantics need measurement.

## Modulation and effects

XMOD assumes OSC1 carrier, OSC2 modulator and maps to Vital FM (phase mode 7).
This is not proof of Poison's cross-modulation algorithm. Ring uses RM from OSC2
(mode 10), taking priority if both are active; lost XMOD is reported. Poison
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
