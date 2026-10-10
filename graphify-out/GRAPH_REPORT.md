# Graph Report - 202ToVital  (2026-10-09)

## Corpus Check
- Corpus is ~11,624 words - fits in a single context window. You may not need a graph.

## Summary
- 279 nodes · 456 edges · 25 communities (18 shown, 7 thin omitted)
- Extraction: 96% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.93)
- Token cost: 3,617 input · 2,630 output

## Community Hubs (Navigation)
- CLI Dependencies
- Preset Format Parsing
- Conversion Core
- Graph Build Dependencies
- Converter Pipeline
- Super Saw Calibration
- CLI Tests
- Audio Analysis Tooling
- LFO and Detune Mapping
- Poison Parser
- Harmonic Layer Experiment
- Controlled Waveform Evidence
- LFO Reset Semantics
- Super Saw Detune Fit
- Pitch Validation
- Super Saw Fallback
- Full-Detune Evidence
- Tempo-Sync Mapping
- Fitted Super Saw Mapping
- Detune Power
- Random Oscillator Phase
- Signed Modulation
- Zero-Detune Policy
- Unison Detune Range
- Package Metadata

## God Nodes (most connected - your core abstractions)
1. `Converter` - 19 edges
2. `convert()` - 19 edges
3. `Profile` - 17 edges
4. `MappingTests` - 14 edges
5. `run_conversion()` - 12 edges
6. `source()` - 12 edges
7. `main()` - 9 edges
8. `CliTests` - 8 edges
9. `main()` - 8 edges
10. `Asymmetric Super Saw Topology` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Asymmetric Super Saw Topology` --semantically_similar_to--> `Asymmetric Super Saw Topology`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `Super Saw Octave Layer Experiment` --semantically_similar_to--> `Phase Reset Octave Sine`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `Symmetric-Unison Fallback` --semantically_similar_to--> `Symmetric-Unison Fallback`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `Remaining Super Saw Fidelity Limits` --semantically_similar_to--> `Remaining Super Saw Fidelity Limits`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `MappingTests` --uses--> `Profile`  [INFERRED]
  tests/test_converter.py → src/poison202_to_vital/profile.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four basic waves have close harmonic structures** — docs_controlled_waveform_review_saw_match, docs_controlled_waveform_review_sine_match, docs_controlled_waveform_review_square_match, docs_controlled_waveform_review_triangle_match [EXTRACTED 1.00]
- **Self-contained Vital state assets** — docs_format_vital_serialization, docs_format_wave_source, docs_format_noise_pcm [EXTRACTED 1.00]
- **Super Saw Octave Layer Diagnostic Experiment** — readme_supersaw_octave_layer, docs_mapping_octave_layer_eligibility, docs_mapping_phase_reset_octave_sine, docs_mapping_octave_layer_center_side_scales, docs_mapping_target_center_harmonic_ratio, docs_mapping_octave_layer_unverified_status [EXTRACTED 1.00]
- **Four basic waves have close harmonic structures** — docs_controlled_waveform_review_saw_match, docs_controlled_waveform_review_sine_match, docs_controlled_waveform_review_square_match, docs_controlled_waveform_review_triangle_match [EXTRACTED 1.00]
- **Self-contained Vital state assets** — docs_format_vital_serialization, docs_format_wave_source, docs_format_noise_pcm [EXTRACTED 1.00]

## Communities (25 total, 7 thin omitted)

### Community 0 - "CLI Dependencies"
Cohesion: 0.07
Nodes (40): argparse, ArgumentParser, base64, contextlib, dataclasses, functools, importlib_metadata, importlib_resources (+32 more)

### Community 1 - "Preset Format Parsing"
Cohesion: 0.07
Nodes (40): Embedded int16 PCM sample, P202 binary framing, P202 parser validation, Pretty Pluck fixture correspondence, Absolute record offset table, Vital registered scalar defaults, Source-derived Vital scalar schema, Single preset and 47-preset bank (+32 more)

### Community 2 - "Conversion Core"
Cohesion: 0.17
Nodes (9): Conversion, convert(), lfo_free_rate_hz(), Map Poison MIX to Vital Blend by matching center/side gain ratios. The Poison…, Approximate Poison's measured free-running LFO RATE response. The controlled…, supersaw_blend(), Profile, MappingTests (+1 more)

### Community 3 - "Graph Build Dependencies"
Cohesion: 0.09
Nodes (20): ast, datetime, graphify_analyze, graphify_build, graphify_cache, graphify_cli, graphify_cluster, graphify_detect (+12 more)

### Community 4 - "Converter Pipeline"
Cohesion: 0.29
Nodes (5): Converter, Return the fitted Poison center and per-side Super Saw gains., Serialize Vital's quadratically scaled unison-detune control. Vital computes…, supersaw_gains(), vital_unison_detune_value()

### Community 5 - "Super Saw Calibration"
Cohesion: 0.11
Nodes (19): Mapping Decisions and Known Fidelity Limits, Asymmetric Super Saw Topology, Asymmetric Topology Eligibility, Five-Voice Auxiliary Group, Center and Side Gain Scaling, Fitted MIX Gains, Isolated Super Saw Reconstruction, LFO2 and MPI2 Destination Omission (+11 more)

### Community 6 - "CLI Tests"
Cohesion: 0.19
Nodes (4): skipUnless, CliTests, encode(), ParserTests

### Community 7 - "Audio Analysis Tooling"
Cohesion: 0.23
Nodes (13): av, numpy, activity(), cosine_similarity(), envelope(), harmonic_spectrum(), main(), major_frequency() (+5 more)

### Community 8 - "LFO and Detune Mapping"
Cohesion: 0.15
Nodes (13): Accidental Approximately 1561-Cent Spread, Default Calibration Profile, Free-running LFO Rate Mapping, LFO Maximum Frequency Profile Control, LFO Minimum Frequency, LFO Rate Exponent Profile Control, Measured LFO Rate Points, Mapping Decisions and Fidelity Limits (+5 more)

### Community 9 - "Poison Parser"
Cohesion: 0.24
Nodes (11): Bank, FormatError, load(), parse(), Preset, Path, Read the tagged little-endian P202 layout observed in the supplied exports.…, An unsupported or malformed source export. (+3 more)

### Community 10 - "Harmonic Layer Experiment"
Cohesion: 0.38
Nodes (7): Octave Layer Center Side Scales, Octave Layer Eligibility, Octave Layer Unverified Status, Phase Reset Octave Sine, Target Center Second to First Harmonic Ratio, 202ToVital Project, Super Saw Octave Layer Experiment

### Community 11 - "Controlled Waveform Evidence"
Cohesion: 0.40
Nodes (6): Relative steady-state harmonic comparison, Saw strong spectral match, Sine strong spectral match, Square strong spectral match, Super Saw mapping deficiency at zero controls, Triangle strong spectral match

### Community 12 - "LFO Reset Semantics"
Cohesion: 0.33
Nodes (6): LFO Reset Policy, Normal LFO Phase-zero Reset, Poison Reset-phase Offset, Poison RETRIG, Random LFO Per-note Reset, Vital Sample-and-hold Generator

### Community 13 - "Super Saw Detune Fit"
Cohesion: 0.33
Nodes (6): JP-8000/Szabo-style normalized Super Saw detune fit. Poison's controlled…, Approximate positive outer-voice separation measured in Poison., Return Vital OSC2 center shift, outer spread, and detune power. The observed…, supersaw_auxiliary_topology(), supersaw_detune_curve(), supersaw_outer_cents()

### Community 14 - "Pitch Validation"
Cohesion: 0.50
Nodes (4): Controlled waveform comparison, Original MIDI 72 versus Vital MIDI 60, Source and Vital output level difference, Pitch-matched Vita renders at MIDI 72

### Community 15 - "Super Saw Fallback"
Cohesion: 0.67
Nodes (3): Fallback Conditions, Symmetric-Unison Fallback, Symmetric-Unison Fallback

### Community 16 - "Full-Detune Evidence"
Cohesion: 0.67
Nodes (3): Sustained Full-Detune Recording, Missing Lowest JP Side Voice, Six Strong Frequency Clusters

### Community 17 - "Tempo-Sync Mapping"
Cohesion: 0.67
Nodes (3): Uncertain 22-entry Tempo Division List, Tempo-sync Mapping, Vital Straight Dotted Triplet Divisions

## Ambiguous Edges - Review These
- `ASCII tags and float32 values` → `Provisional filter selector mapping`  [AMBIGUOUS]
  docs/format.md · relation: conceptually_related_to

## Knowledge Gaps
- **41 isolated node(s):** `poison202-to-vital`, `Pitch-matched Vita renders at MIDI 72`, `Sine strong spectral match`, `Square strong spectral match`, `Triangle strong spectral match` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 106 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ASCII tags and float32 values` and `Provisional filter selector mapping`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Converter` connect `Converter Pipeline` to `CLI Dependencies`, `Poison Parser`, `Conversion Core`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `Profile` connect `Conversion Core` to `CLI Dependencies`, `Converter Pipeline`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `convert()` connect `Conversion Core` to `CLI Dependencies`, `Poison Parser`, `Converter Pipeline`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Converter` (e.g. with `Preset` and `Profile`) actually correct?**
  _`Converter` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Profile` (e.g. with `Converter` and `lfo_free_rate_hz()`) actually correct?**
  _`Profile` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `poison202-to-vital`, `Pitch-matched Vita renders at MIDI 72`, `Sine strong spectral match` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._