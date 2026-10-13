# Poison-202 2.5.7 IPA findings used by the converter

This document records only evidence that affects 202ToVital. It distinguishes
facts recovered from the IPA from conversion hypotheses; an exposed class or
symbol name is not proof of its numerical law.

## Factory presets and P202 serialization

- `PresetsNew.plist` contains 594 presets across banks sized
  100/100/100/100/94/100.
- The factory union contains 109 fields: `name`, `tags`, and 107 parameters.
- Observed P202 records contain 106 tagged float32 parameters. All 106 tags have
  a unique factory-key counterpart in `poison_schema.P202_TAG_TO_FACTORY_KEY`.
- `TEMPOSYNC` is the sole factory parameter not present in observed P202 files.
  P202 does preserve `TSL1`/`TEMPOLFO1`, `TSL2`/`TEMPOLFO2`, and
  `TSDE`/`TEMPODELAY` independently.
- The 16-byte record prefix is a 15-byte NUL-padded name followed by a persistent
  zero-based source slot. It is not a 16-byte name field.
- Parameter entries are four printable tag bytes followed by a little-endian
  IEEE-754 float32. Their order is not semantic.

The converter now exposes the source slot and long factory key in inspection and
conversion reports. It continues to preserve unknown well-framed tags rather
than requiring the 2.5.7 schema.

## Oscillator table and Super Saw boundary

`jimsawopen64x1024.data` is 64 contiguous tables of 1,024 little-endian float32
samples. Spectral and continuity checks identify them as pitch-indexed,
band-limited saw tables. It is therefore neither a 64-frame morph wavetable nor
a complete rendered Super Saw oscillator.

The binaries separately expose `PoisonDSP::computeSuperSawDetuneForOsc(int)`,
which supports treating Super Saw detune as runtime DSP rather than information
encoded in `jimsawopen64x1024.data`. Consequently 202ToVital does not import that
file as a Vital morph wavetable and does not claim that its packaged JP-inspired
single-cycle asset reproduces Poison's internal table bank.

## What the binaries do and do not establish

The main app and Audio Unit executable expose names consistent with parameter
ramps, pitch and portamento rendering, TVA application, biquad filtering, tempo
sync, Super Saw detune, reverb, and limiting. Their relevant Mach-O code pages
are FairPlay-encrypted (`cryptid=1`), so the implementations and numeric transfer
functions were not recoverable from this IPA.

This evidence confirms subsystem existence only. Envelope curves, filter laws,
fine-tune scale, modulation depths, effect algorithms, exact Super Saw voice
placement, smoothing, and gain staging remain measured approximations or
explicit profile hypotheses. The converter reports them that way.

## UI evidence

The rotary-control atlas contains frames `V0` through `V170`, consistent with a
171-position visual control scale. Waveform glyph/resource names corroborate the
available oscillator/LFO choices, but UI artwork does not establish DSP enum
values or parameter curves. No conversion law is derived from the atlas alone.
