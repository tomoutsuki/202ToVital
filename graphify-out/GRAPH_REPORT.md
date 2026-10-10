# Graph Report - 202ToVital  (2026-10-09)

## Corpus Check
- Corpus is ~11,225 words - fits in a single context window. You may not need a graph.

## Summary
- 265 nodes · 436 edges · 22 communities (15 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Preset Format Parsing
- Conversion Core
- Graph Build Dependencies
- CLI and Asset Utilities
- Super Saw Calibration
- Conversion Functions
- Converter Pipeline
- CLI Tests
- Audio Analysis Tooling
- Controlled Waveform Evidence
- LFO Reset Semantics
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
2. `convert()` - 18 edges
3. `Profile` - 16 edges
4. `MappingTests` - 13 edges
5. `run_conversion()` - 12 edges
6. `source()` - 11 edges
7. `main()` - 9 edges
8. `CliTests` - 8 edges
9. `main()` - 8 edges
10. `Asymmetric Super Saw Topology` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Asymmetric Super Saw Topology` --semantically_similar_to--> `Asymmetric Super Saw Topology`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `Symmetric-Unison Fallback` --semantically_similar_to--> `Symmetric-Unison Fallback`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `Remaining Super Saw Fidelity Limits` --semantically_similar_to--> `Remaining Super Saw Fidelity Limits`  [INFERRED] [semantically similar]
  README.md → docs/mapping.md
- `MappingTests` --uses--> `Profile`  [INFERRED]
  tests/test_converter.py → src/poison202_to_vital/profile.py
- `Preserved unmapped tags` --shares_data_with--> `Conversion report`  [EXTRACTED]
  docs/mapping.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four basic waves have close harmonic structures** — docs_controlled_waveform_review_saw_match, docs_controlled_waveform_review_sine_match, docs_controlled_waveform_review_square_match, docs_controlled_waveform_review_triangle_match [EXTRACTED 1.00]
- **Self-contained Vital state assets** — docs_format_vital_serialization, docs_format_wave_source, docs_format_noise_pcm [EXTRACTED 1.00]

## Communities (22 total, 7 thin omitted)

### Community 0 - "Preset Format Parsing"
Cohesion: 0.07
Nodes (40): Embedded int16 PCM sample, P202 binary framing, P202 parser validation, Pretty Pluck fixture correspondence, Absolute record offset table, Vital registered scalar defaults, Source-derived Vital scalar schema, Single preset and 47-preset bank (+32 more)

### Community 1 - "Conversion Core"
Cohesion: 0.09
Nodes (28): contextlib, dataclasses, io, math, pathlib, Conversion, Best-effort mappings; all unknown Poison laws are reported, never asserted…, JP-8000/Szabo-style normalized Super Saw detune fit. Poison's controlled… (+20 more)

### Community 2 - "Graph Build Dependencies"
Cohesion: 0.07
Nodes (25): argparse, ast, datetime, graphify_analyze, graphify_build, graphify_cache, graphify_cli, graphify_cluster (+17 more)

### Community 3 - "CLI and Asset Utilities"
Cohesion: 0.11
Nodes (25): ArgumentParser, base64, functools, importlib_resources, os, random, json_bytes(), main() (+17 more)

### Community 4 - "Super Saw Calibration"
Cohesion: 0.08
Nodes (27): Accidental Approximately 1561-Cent Spread, Asymmetric Super Saw Topology, Asymmetric Topology Eligibility, Five-Voice Auxiliary Group, Default Calibration Profile, Fitted MIX Gains, Free-running LFO Rate Mapping, LFO2 and MPI2 Destination Omission (+19 more)

### Community 5 - "Conversion Functions"
Cohesion: 0.19
Nodes (8): convert(), lfo_free_rate_hz(), Map Poison MIX to Vital Blend by matching center/side gain ratios. The Poison…, Approximate Poison's measured free-running LFO RATE response. The controlled…, supersaw_blend(), Profile, MappingTests, source()

### Community 6 - "Converter Pipeline"
Cohesion: 0.28
Nodes (5): Converter, Return the fitted Poison center and per-side Super Saw gains., Serialize Vital's quadratically scaled unison-detune control. Vital computes…, supersaw_gains(), vital_unison_detune_value()

### Community 7 - "CLI Tests"
Cohesion: 0.19
Nodes (4): skipUnless, CliTests, encode(), ParserTests

### Community 8 - "Audio Analysis Tooling"
Cohesion: 0.23
Nodes (13): av, numpy, activity(), cosine_similarity(), envelope(), harmonic_spectrum(), main(), major_frequency() (+5 more)

### Community 9 - "Controlled Waveform Evidence"
Cohesion: 0.40
Nodes (6): Relative steady-state harmonic comparison, Saw strong spectral match, Sine strong spectral match, Square strong spectral match, Super Saw mapping deficiency at zero controls, Triangle strong spectral match

### Community 10 - "LFO Reset Semantics"
Cohesion: 0.33
Nodes (6): LFO Reset Policy, Normal LFO Phase-zero Reset, Poison Reset-phase Offset, Poison RETRIG, Random LFO Per-note Reset, Vital Sample-and-hold Generator

### Community 11 - "Pitch Validation"
Cohesion: 0.50
Nodes (4): Controlled waveform comparison, Original MIDI 72 versus Vital MIDI 60, Source and Vital output level difference, Pitch-matched Vita renders at MIDI 72

### Community 12 - "Super Saw Fallback"
Cohesion: 0.67
Nodes (3): Fallback Conditions, Symmetric-Unison Fallback, Symmetric-Unison Fallback

### Community 13 - "Full-Detune Evidence"
Cohesion: 0.67
Nodes (3): Sustained Full-Detune Recording, Missing Lowest JP Side Voice, Six Strong Frequency Clusters

### Community 14 - "Tempo-Sync Mapping"
Cohesion: 0.67
Nodes (3): Uncertain 22-entry Tempo Division List, Tempo-sync Mapping, Vital Straight Dotted Triplet Divisions

## Ambiguous Edges - Review These
- `ASCII tags and float32 values` → `Provisional filter selector mapping`  [AMBIGUOUS]
  docs/format.md · relation: conceptually_related_to

## Knowledge Gaps
- **39 isolated node(s):** `poison202-to-vital`, `Pitch-matched Vita renders at MIDI 72`, `Sine strong spectral match`, `Square strong spectral match`, `Triangle strong spectral match` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 100 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ASCII tags and float32 values` and `Provisional filter selector mapping`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Converter` connect `Converter Pipeline` to `Conversion Core`, `Conversion Functions`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `Profile` connect `Conversion Functions` to `Conversion Core`, `CLI and Asset Utilities`, `Converter Pipeline`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `convert()` connect `Conversion Functions` to `Conversion Core`, `CLI and Asset Utilities`, `Converter Pipeline`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Converter` (e.g. with `Preset` and `Profile`) actually correct?**
  _`Converter` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Profile` (e.g. with `Converter` and `lfo_free_rate_hz()`) actually correct?**
  _`Profile` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `poison202-to-vital`, `Pitch-matched Vita renders at MIDI 72`, `Sine strong spectral match` to the rest of the system?**
  _39 weakly-connected nodes found - possible documentation gaps or missing edges._