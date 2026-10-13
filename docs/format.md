# Observed preset formats

## Poison P202 binary framing

Evidence: 14 supplied P202 files containing 60 records, cross-checked against
Poison-202 2.5.7's factory preset plist. The following describes those exports,
not every Poison version.

| Byte offset | Observed encoding | Meaning |
| --- | --- | --- |
| 0 | four bytes `P202` | Magic |
| 4 | little-endian uint16 | Preset count: 1 or 47 |
| 6 | little-endian uint16, value 16 | Assumed absolute offset-table start |
| 8 | eight zero bytes | Reserved; meaning unknown |
| 16 | count little-endian uint32 values | Absolute record offsets |
| record + 0 | 15 bytes | NUL-padded preset name (UTF-8 in observed files) |
| record + 15 | uint8 | Retained zero-based source-bank slot |
| record + 16 | repeated 8-byte entries | Four ASCII tag bytes followed by little-endian IEEE-754 float32 |
| record end - 4 | `####` | Terminator |

Each supplied record is 868 bytes: 15-byte name + one-byte slot + 106 tagged
values + terminator.
Single record starts at 20; bank records start at 204 and increase by 868.
The slot byte is exactly 0..46 in the supplied 47-record bank. Single exports do
not reset it: Pretty Pluck retains slot 38 and matches zero-based bank record 38.
The parser exposes this as `source_slot` and uses offsets and record framing,
not a hardcoded number/order of tags.
It rejects unsupported header layouts, duplicate tags, NaN/Inf, invalid offsets,
trailing bytes, non-ASCII tags and truncation. Unknown well-framed tags survive
inspection and conversion reports. Reserved header bytes survive in the report.
Maximum supported count is 300, based on the supplied Poison feature inventory.
UTF-8 names fall back to Latin-1 when decoding fails; encoding is not confirmed.

Pretty Pluck (bank entry 39) has exactly the same 106 decoded values as the
single preset. Its byte at record offset 15 is `0x26` (38), which was previously
misidentified as nonzero name padding.

## Poison 2.5.7 factory schema

`PresetsNew.plist` contains 594 presets in six banks of 100, 100, 100, 100, 94,
and 100 entries. Its union has 109 keys: `name`, `tags`, and 107 parameter keys.
Every one of the 106 P202 tags maps one-to-one to a long factory key; the mapping
is available at runtime as `poison_schema.P202_TAG_TO_FACTORY_KEY` and is emitted
by `202tovital inspect`. Record tag order is not semantic and one supplied
rewritten file uses a different order.

The only factory parameter absent from observed P202 records is `TEMPOSYNC`.
Modern P202 data instead carries three independent switches: `TSL1` maps to
`TEMPOLFO1`, `TSL2` to `TEMPOLFO2`, and `TSDE` to `TEMPODELAY`. The converter
must not synthesize a shared `TEMPOSYNC` value.

Tags suggest meaning; storage alone does not prove the corresponding UI mapping.
Examples: `O1PI` stores semitone-like integers -24..24, `O1TU` stores signed
fractions, `F1CU` stores fractions 0..1, `GAIN` reaches 1.88473. They are **not
7-bit MIDI CC values**. `F1TY`/`F2TY` range 0..5 despite five documented filter
responses; the default profile hypothesizes 0=off, 1..5=LP/BP/HP/Peak/Notch.

`202tovital inspect` preserves those float32 values verbatim and adds conservative
interpretations for known controls. For normalized LFO controls it reports an
approximate 7-bit MIDI position; signed depths use `(value + 1) * 63.5`. This is
a UI-scale estimate, not a MIDI byte decoded from the file. A single preset is
shown in detail by default, `--preset` selects one bank entry, and `--json`
includes record framing, source slot, raw parameters, factory keys and decoded
annotations.

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
