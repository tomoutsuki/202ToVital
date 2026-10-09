# Observed preset formats

## Poison P202 binary framing

Evidence: `../.materials/SinglePreset.p202` (888 bytes) and
`../.materials/SynthUserBank.p202` (41,000 bytes). Both were supplied by the user.
The following describes these exports, not every Poison version.

| Byte offset | Observed encoding | Meaning |
| --- | --- | --- |
| 0 | four bytes `P202` | Magic |
| 4 | little-endian uint16 | Preset count: 1 or 47 |
| 6 | little-endian uint16, value 16 | Assumed absolute offset-table start |
| 8 | eight zero bytes | Reserved; meaning unknown |
| 16 | count little-endian uint32 values | Absolute record offsets |
| record + 0 | 16 bytes | NUL-terminated name area; trailing bytes can be nonzero |
| record + 16 | repeated 8-byte entries | Four ASCII tag bytes followed by little-endian IEEE-754 float32 |
| record end - 4 | `####` | Terminator |

Each supplied record is 868 bytes: name area + 106 tagged values + terminator.
Single record starts at 20; bank records start at 204 and increase by 868.
The parser uses offsets and record framing, not a hardcoded number/order of tags.
It rejects unsupported header layouts, duplicate tags, NaN/Inf, invalid offsets,
trailing bytes, non-ASCII tags and truncation. Unknown well-framed tags survive
inspection and conversion reports. Reserved header bytes survive in the report.
Maximum supported count is 300, based on the supplied Poison feature inventory.
UTF-8 names fall back to Latin-1 when decoding fails; encoding is not confirmed.

Pretty Pluck (bank entry 39) has exactly the same 106 decoded values as the
single preset. Name padding differs from zero, so treating all 16 bytes as a
plain printable name would be incorrect.

Tags suggest meaning; storage alone does not prove the corresponding UI mapping.
Examples: `O1PI` stores semitone-like integers -24..24, `O1TU` stores signed
fractions, `F1CU` stores fractions 0..1, `GAIN` reaches 1.88473. They are **not
7-bit MIDI CC values**. `F1TY`/`F2TY` range 0..5 despite five documented filter
responses; the default profile hypothesizes 0=off, 1..5=LP/BP/HP/Peak/Notch.

## Vital serialization

Reference source revision: `636ca0ef517a4db087a6a08a6a8a5e704e21f836`, from
`../.materials/vital/vital`. That checkout advertises Vital 1.0.6 in
`standalone/JuceLibraryCode/JuceHeader.h:53`. Supplied community presets include
1.5.5; the converter targets the inspected 1.0.6 format for broader compatibility.

- `src/common/load_save.cpp:98` (`stateToJson`) emits metadata and `settings`.
- `src/common/load_save.cpp:153` (`loadControls`) restores omitted scalar controls
  to registered defaults. This allows compact output without cloning a demo preset.
- `src/common/load_save.cpp:170` (`loadModulations`) loads source/destination
  connections in array order, corresponding to numbered modulation controls.
- `src/common/load_save.cpp:1027` (`jsonToState`) requires sample, wavetable, LFO,
  and modulation state. All four are explicitly initialized by the converter.
- `src/common/synth_parameters.cpp:353` declares envelope times with quartic
  scaling: serialized value = seconds**0.25. LFO frequency uses log2(Hz).
  Filter cutoff is MIDI note number; oscillator tune uses semitones (displayed cents).
  Master volume is (dB + 80)**2. These are Vital laws, not Poison laws.
- `src/common/wavetable/wave_source.cpp:194` stores `wave_data` as base64 native
  float32 samples. On the target little-endian platforms the converter uses
  2048 little-endian samples per frame, embedded under a `Wave Source` component.
- `src/synthesis/producers/sample_source.cpp:307` stores sample data as base64
  int16 PCM plus length/rate. The converter embeds its own noise when required.
- `src/interface/editor_sections/bank_exporter.cpp:576` creates a ZIP. Presets
  live at `BankName/Presets/Filename.vital`; no manifest is required by that exporter.

The generated scalar schema is reproducible with
`python3 tools/extract_vital_schema.py ../.materials/vital/vital`.
It describes the inspected source revision. Some control ranges differ in newer
Vita builds (destination upper bounds and wavetable position); the converter's
used values lie in both ranges.
